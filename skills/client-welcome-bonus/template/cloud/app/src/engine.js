// Promo engine on D1. Same rules as the local app / skill:
// - participants = clients registered with the partner in [start, end]
// - a condition (FTD / KYC) has no event date in the API, so it counts when first observed
//   true while the window is open (+1 day grace); clients already qualified at launch are excluded
//   (except test promotions)
// - every payout row holds its idempotency key before sending; a row is claimed atomically before each
//   attempt, so the cron and a user click can never send the same payout twice
import { ApiError } from "./exness.js";

export const CONDITIONS = { ftd: "ftd_received", kyc: "kyc_passed" };
export const LABELS = { ftd: "First deposit (FTD)", kyc: "KYC verification" };

// ---- instruments (for the "Traded symbols" chart) ----
const FX = new Set("USD EUR GBP JPY CHF CAD AUD NZD SGD HKD NOK SEK DKK PLN CZK HUF TRY ZAR MXN CNH RUB INR THB ILS SAR AED BRL IDR KRW TWD MYR PHP".split(" "));
const CRYPTO = /^(BTC|ETH|LTC|XRP|BCH|ADA|DOT|SOL|DOGE|BNB|LINK|UNI|XLM|XTZ|AVAX|MATIC|TRX|SHIB|ATOM|FIL|AAVE|ZEC|XMR|DASH|EOS|NEAR|TON|USDT)/;
export const normSym = (s) => String(s || "").replace(/[a-z_.#]+$/, "").toUpperCase(); // EURUSDm -> EURUSD
export function symbolGroup(s) {
  s = normSym(s);
  if (/^(XAU|XAG|XPT|XPD)/.test(s)) return "metals";
  if (/(OIL|^XNG|NGAS|BRENT|WTI)/.test(s)) return "energy";
  if (CRYPTO.test(s)) return "crypto";
  if (s.length === 6 && FX.has(s.slice(0, 3)) && FX.has(s.slice(3))) return "forex";
  if (/^(US30|US500|USTEC|UK100|DE30|DE40|FR40|JP225|AUS200|HK50|STOXX50|IN50|NAS100|SPX500|GER40)/.test(s)) return "indices";
  return "stocks";
}
export const condLabel = (p) => LABELS[p.condition] || p.condition;
const MT = new Set(["mt4", "mt5"]);
const SAME_KEY_RETRY = new Set(["TRANSFER_OUTCOME_UNKNOWN", "SYSTEM_INTERNAL_ERROR", "SYSTEM_TEMPORARY_UNAVAILABLE",
  "REQUEST_RATE_LIMIT", "TRANSFER_LIMIT_REACHED"]);
const NEW_KEY_RETRY = new Set(["OPERATION_NOT_ALLOWED"]); // can be transient; it is a definitive rejection, so a new key is safe
const IN_FLIGHT = ["queued", "sending", "retry", "processing"];
// EXD payouts go through POST /v1/partnership/exd/transfers/clients. The API only answers
// "PENDING" and has no status endpoint, so an accepted EXD transfer is final for us: status 'sent'.
export const CURRENCIES = ["USD", "EXD"];
const PAID = "('done','sent')";
const COMMITTED = "('done','sent','queued','sending','retry','processing')";
const isPaid = (s) => s === "done" || s === "sent";
export const fmtAmt = (n, cur) => (cur === "EXD" ? `${Number(n).toFixed(2)} EXD` : `$${Number(n).toFixed(2)}`);
const RETRY_DELAY_MS = 30_000;
const CLAIM_MS = 60_000;
const AUTO_BATCH = 10; // max automatic payouts per promo per cron run

export class EngineError extends Error {}

const nowIso = () => new Date().toISOString().slice(0, 19) + "Z";
const today = () => new Date().toISOString().slice(0, 10);
const addDays = (iso, n) => { const d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
const round2 = (x) => Math.round(x * 100) / 100;

export class Engine {
  constructor(env, api) { this.db = env.DB; this.api = api; }

  // ---------- API data ----------
  summary() { return this.api.call("GET", "/v1/partnership/partner/summary"); }

  async wallet() {
    if (this.api.demo) return "DEMO-WALLET"; // never cache demo values
    const m = await this.db.prepare("SELECT v FROM meta WHERE k='wallet'").first();
    if (m) return m.v;
    const accs = ((await this.summary()).accounts || []).filter((a) => a.account_type === "partner" && !a.archived);
    if (!accs.length) throw new EngineError("No Partner Reward Wallet found on this account");
    await this.db.prepare("INSERT OR REPLACE INTO meta (k, v) VALUES ('wallet', ?)").bind(accs[0].account).run();
    return accs[0].account;
  }

  async balance() { return Number((await this.api.call("GET", `/v1/accounts/${await this.wallet()}/balance`)).amount); }

  async partnerUid() {
    if (this.api.demo) return "demo";
    const m = await this.db.prepare("SELECT v FROM meta WHERE k='partner_uid'").first();
    if (m) return m.v;
    const uid = (await this.summary()).uid;
    if (!uid) throw new EngineError("The API didn't return the partner ID");
    await this.db.prepare("INSERT OR REPLACE INTO meta (k, v) VALUES ('partner_uid', ?)").bind(uid).run();
    return uid;
  }

  clients(from, to) {
    return this.api.paged("/v1/partnership/reports/clients", from ? `reg_date_from=${from}&reg_date_to=${to}` : "");
  }

  accounts(uid) {
    return this.api.paged("/v1/partnership/reports/clients/accounts", uid ? `client_uid=${encodeURIComponent(uid)}` : "");
  }

  async payoutAccount(uid) {
    const c = await this.db.prepare("SELECT account FROM accounts WHERE uid=?").bind(uid).first();
    if (c) return c.account;
    const rows = (await this.accounts(uid))
      .filter((r) => r.client_uid && (uid.startsWith(r.client_uid) || r.client_uid.startsWith(uid.slice(0, 8))))
      .filter((r) => !MT.has((r.platform || "").toLowerCase()))
      .sort((a, b) => (b.client_account_last_trade || "").localeCompare(a.client_account_last_trade || ""));
    if (!rows.length) return null;
    await this.db.prepare("INSERT OR REPLACE INTO accounts (uid, account) VALUES (?, ?)").bind(uid, rows[0].client_account).run();
    return rows[0].client_account;
  }

  // ---------- promos ----------
  async get(id) {
    const p = await this.db.prepare("SELECT * FROM promos WHERE id=?").bind(id).first();
    if (!p) throw new EngineError(`Promo ${id} not found`);
    p.baseline = JSON.parse(p.baseline || "[]");
    p.test = !!p.test;
    p.auto_pay = !!p.auto_pay;
    p.currency = p.currency || "USD";
    return p;
  }

  phase(p) {
    if (p.status === "ended") return "ended";
    if (today() < p.start) return "scheduled";
    if (today() > p.end) return "completed";
    return "active";
  }

  // Who takes part: new = registered with the partner in [start, end]; existing = registered before the start date.
  async participants(p) {
    if (today() < p.start) return [];
    if (p.audience === "existing") return (await this.clients()).filter((c) => (c.reg_date || "").slice(0, 10) < p.start);
    return this.clients(p.start, p.end);
  }

  async create({ title, amount, days, condition = "ftd", budget = null, start = null, test = false, autoPay = false, audience = "new", currency = "USD" }) {
    if (autoPay) throw new EngineError("Automatic payouts are not implemented in this version");
    if (!["new", "existing"].includes(audience)) throw new EngineError("Unknown audience");
    if (!CURRENCIES.includes(currency)) throw new EngineError("Unknown currency");
    if (currency === "EXD" && autoPay) throw new EngineError("Automatic payouts aren't available for EXD yet (the API has no EXD transfer status)");
    amount = Number(amount); days = Number(days); budget = budget ? Number(budget) : null;
    if (!LABELS[condition]) throw new EngineError("Unknown condition");
    if (!(amount > 0 && amount <= 10000) || !(days >= 1 && days <= 365)) throw new EngineError("Amount must be 0–10,000 and duration 1–365 days");
    if (budget !== null && budget < amount) throw new EngineError("Budget must cover at least one payout");
    if (autoPay && !budget) throw new EngineError("Automatic payouts need a budget");
    start = start || today();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(start)) throw new EngineError("Bad start date");
    const end = addDays(start, days - 1);
    if (test) {
      if (amount > 1) throw new EngineError(`Test promotions pay at most ${fmtAmt(1, currency)} per client`);
      if (!budget || budget > 10) throw new EngineError(`Test promotions need a budget of at most ${fmtAmt(10, currency)}`);
      if (end < today()) throw new EngineError("Test promotion period must include today");
    } else if (start < today()) throw new EngineError("Start date can't be in the past");
    const wallet = await this.wallet();
    const flag = CONDITIONS[condition];
    const baseline = test ? [] : (await this.clients()).filter((c) => c[flag]).map((c) => c.client_uid);
    const id = "p" + crypto.randomUUID().replace(/-/g, "").slice(0, 6);
    await this.db.prepare(`INSERT INTO promos (id, title, condition, amount, start, "end", budget, wallet, status, test, baseline, created_at, auto_pay, audience, currency)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)`)
      .bind(id, String(title || "Client bonus").slice(0, 100), condition, amount, start, end, budget, wallet, test ? 1 : 0,
        JSON.stringify(baseline), nowIso(), autoPay ? 1 : 0, audience, currency).run();
    return { id };
  }

  // Orders report accepts periods shorter than a month -> fetch in 28-day chunks.
  async orders(from, to) {
    const out = [];
    for (let a = from; a <= to; a = addDays(a, 28)) {
      const b = addDays(a, 27) < to ? addDays(a, 27) : to;
      out.push(...(await this.api.paged("/v1/partnership/reports/orders", `date_from=${a}&date_to=${b}`, 1000)));
    }
    return out;
  }

  // Orders in the promo period + the account -> client map (for the "Traded symbols" chart).
  async promoOrders(p) {
    const to = today() < p.end ? today() : p.end;
    const [orders, accs] = await Promise.all([this.orders(p.start, to), this.accounts()]);
    return { orders, accs };
  }

  async scan(id) {
    const p = await this.get(id);
    const rows = await this.participants(p);
    const flag = CONDITIONS[p.condition];
    const met = (c) => c[flag];
    const open = p.status === "active" && today() <= addDays(p.end, 1);
    const base = new Set(p.baseline);
    const stmts = [];
    if (open) {
      for (const c of rows) {
        if (met(c) && !base.has(c.client_uid)) {
          stmts.push(this.db.prepare("INSERT OR IGNORE INTO qualified (promo_id, uid, observed, at) VALUES (?, ?, ?, ?)")
            .bind(id, c.client_uid, today(), nowIso()));
        }
      }
    }
    stmts.push(this.db.prepare("UPDATE promos SET last_scan=? WHERE id=?").bind(nowIso(), id));
    await this.db.batch(stmts);
    return rows;
  }

  async committed(id) {
    const r = await this.db.prepare(`SELECT COALESCE(SUM(amount),0) s FROM payouts WHERE promo_id=? AND status IN ${COMMITTED}`).bind(id).first();
    return r.s;
  }

  async detail(id, rescan = true) {
    const p = await this.get(id);
    const rows = rescan ? await this.scan(id) : await this.participants(p);
    const flag = CONDITIONS[p.condition];
    const q = new Map((await this.db.prepare("SELECT uid, observed FROM qualified WHERE promo_id=?").bind(id).all()).results.map((r) => [r.uid, r.observed]));
    const pays = new Map((await this.db.prepare("SELECT * FROM payouts WHERE promo_id=?").bind(id).all()).results.map((r) => [r.uid, r]));
    const base = new Set(p.baseline);
    let budgetLeft = p.budget ? p.budget - (await this.committed(id)) : null;
    const participants = [];
    for (const c of rows) {
      const uid = c.client_uid, pay = pays.get(uid);
      let state;
      if (pay) state = ["queued", "retry"].includes(pay.status) ? "sending" : pay.status;
      else if (q.has(uid)) state = "to_pay";
      else if (base.has(uid)) state = "excluded";
      else if (c[flag]) state = "missed";
      else state = "waiting";
      const row = {
        uid, short: uid.slice(0, 8), reg_date: c.reg_date, country: c.client_country,
        kyc: c.kyc_passed, ftd: c.ftd_received, ftt: c.ftt_made, reward_usd: Number(c.reward_usd || 0), state,
        qualified_on: q.get(uid) || null, account: pay?.account || null, transfer_id: pay?.transfer_id || null,
        error: pay?.status === "retry" ? null : pay?.error || null,
      };
      if (["to_pay", "failed", "rejected"].includes(state)) {
        // EXD goes to the client (by client ID), not to a trading account
        if (p.currency === "EXD") row.account = "EXD";
        else row.account = row.account || (await this.payoutAccount(uid));
        if (!row.account) row.blocked = "No account that can receive transfers (MT4/MT5 only)";
        else if (budgetLeft !== null && budgetLeft < p.amount) row.blocked = "Budget exhausted";
        else if (budgetLeft !== null) budgetLeft -= p.amount;
      }
      participants.push(row);
    }
    const all = [...pays.values()];
    const spent = all.filter((x) => isPaid(x.status)).reduce((s, x) => s + x.amount, 0);
    const flight = all.filter((x) => IN_FLIGHT.includes(x.status));
    const earned = participants.reduce((s, r) => s + r.reward_usd, 0);
    const fresh = await this.get(id);
    return {
      id: p.id, title: p.title, condition: p.condition, amount: p.amount, start: p.start, end: p.end, budget: p.budget,
      wallet: p.wallet, created_at: p.created_at, test: p.test, condition_label: condLabel(p),
      audience: p.audience || "new", currency: p.currency,
      auto_pay: p.auto_pay, auto_note: fresh.auto_note || null,
      phase: this.phase(p), last_scan: fresh.last_scan, paying: flight.some((x) => x.status !== "processing"),
      stats: {
        participants: participants.length, qualified: q.size,
        paid: all.filter((x) => isPaid(x.status)).length, in_flight: flight.length,
        failed: all.filter((x) => ["failed", "rejected"].includes(x.status)).length,
        spent: round2(spent), in_flight_amount: round2(flight.reduce((s, x) => s + x.amount, 0)),
        to_pay: participants.filter((r) => ["to_pay", "failed", "rejected"].includes(r.state) && !r.blocked).length,
        earned: round2(earned), net: round2(earned - spent),
      },
      participants,
    };
  }

  // Per-day trading of the promo's participants (API rewards report) + bonuses paid by the partner.
  async metrics(id) {
    const p = await this.get(id);
    const to = today() < p.start ? null : today() < p.end ? today() : p.end; // charts stop at the promo end
    const days = [];
    if (to) for (let d = p.start; d <= to; d = addDays(d, 1)) days.push({ date: d, lots: 0, mln: 0, orders: 0, reward: 0, bonus: 0 });
    const idx = new Map(days.map((d, i) => [d.date, i]));
    const clients = to ? await this.participants(p) : [];
    const uids = new Set(clients.map((c) => c.client_uid));
    const rows = uids.size ? await this.api.paged("/v1/partnership/reports/rewards",
      `aggregate_by=day&reward_date_from=${p.start}&reward_date_to=${to}`) : [];
    const per = {};
    for (const r of rows) {
      if (!uids.has(r.client_uid)) continue;
      const i = idx.get((r.reward_date || "").slice(0, 10));
      if (i === undefined) continue;
      const v = { lots: Number(r.volume_lots || 0), mln: Number(r.volume_mln_usd || 0), orders: Number(r.orders_count || 0), reward: Number(r.reward_usd || 0) };
      const c = (per[r.client_uid] ||= { lots: 0, mln: 0, orders: 0, reward: 0 });
      for (const k in v) { days[i][k] += v[k]; c[k] += v[k]; }
    }
    const paid = (await this.db.prepare(`SELECT amount, finished_at, sent_at FROM payouts WHERE promo_id=? AND status IN ${PAID}`).bind(id).all()).results;
    for (const x of paid) {
      if (!days.length) break;
      const d = (x.finished_at || x.sent_at || "").slice(0, 10);
      const i = idx.has(d) ? idx.get(d) : d < p.start ? 0 : days.length - 1;
      days[i].bonus += x.amount;
    }
    let symbols = [];
    if (to) {
      const pre = await this.promoOrders(p);
      // What participants traded in the promo period, by symbol (orders report; suffixes like "m" stripped)
      const pref = new Set(clients.map((c) => c.client_uid.slice(0, 8)));
      const accUid = new Map(pre.accs.map((a) => [String(a.client_account), (a.client_uid || "").slice(0, 8)]));
      const bySym = new Map();
      for (const o of pre.orders) {
        const u = accUid.get(String(o.client_account));
        if (!u || !pref.has(u)) continue;
        const s = normSym(o.symbol);
        const x = bySym.get(s) || { symbol: s, group: symbolGroup(s), lots: 0, orders: 0, clients: new Set() };
        x.lots += Number(o.volume_lots || 0); x.orders++; x.clients.add(u); bySym.set(s, x);
      }
      symbols = [...bySym.values()].map((x) => ({ ...x, lots: round2(x.lots), clients: x.clients.size })).sort((a, b) => b.lots - a.lots || b.orders - a.orders);
    }
    const sum = (k) => round2(days.reduce((s, d) => s + d[k], 0));
    for (const d of days) { d.lots = round2(d.lots); d.mln = Math.round(d.mln * 1e4) / 1e4; d.reward = round2(d.reward); d.bonus = round2(d.bonus); }
    for (const c of Object.values(per)) { c.lots = round2(c.lots); c.reward = round2(c.reward); c.mln = Math.round(c.mln * 1e4) / 1e4; }
    return {
      days, per_client: per, symbols,
      totals: { lots: sum("lots"), mln: Math.round(days.reduce((s, d) => s + d.mln, 0) * 1e4) / 1e4, orders: sum("orders"),
        reward: sum("reward"), bonus: sum("bonus"), traders: Object.keys(per).length, participants: uids.size },
    };
  }

  async list() {
    const promos = (await this.db.prepare("SELECT * FROM promos ORDER BY created_at DESC").all()).results;
    const q = (await this.db.prepare("SELECT promo_id, COUNT(*) n FROM qualified GROUP BY promo_id").all()).results;
    const pd = (await this.db.prepare(`SELECT promo_id, COUNT(*) n, SUM(amount) s FROM payouts WHERE status IN ${PAID} GROUP BY promo_id`).all()).results;
    const qn = Object.fromEntries(q.map((r) => [r.promo_id, r.n]));
    const pdn = Object.fromEntries(pd.map((r) => [r.promo_id, r]));
    return promos.map((p) => ({
      id: p.id, title: p.title, condition: p.condition, amount: p.amount, start: p.start, end: p.end, budget: p.budget,
      test: !!p.test, auto_pay: !!p.auto_pay, audience: p.audience || "new", phase: this.phase(p), qualified: qn[p.id] || 0,
      paid: pdn[p.id]?.n || 0, spent: round2(pdn[p.id]?.s || 0), condition_label: condLabel(p), hidden: !!p.hidden,
      currency: p.currency || "USD",
    }));
  }

  async end(id) {
    await this.scan(id);
    await this.db.prepare("UPDATE promos SET status='ended', auto_pay=0, ended_at=? WHERE id=?").bind(nowIso(), id).run();
  }

  async setAutoPay() { throw new EngineError("Automatic payouts are not implemented in this version"); }
  async startPayout() { throw new EngineError("Money transfers are not implemented in this version"); }
}
