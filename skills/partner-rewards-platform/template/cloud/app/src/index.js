// Partner Rewards Studio — Cloudflare Worker (API + static UI + cron).
import { authenticate, AuthError } from "./access.js";
import { Engine, EngineError, LABELS } from "./engine.js";
import { ApiError, DemoExness, Exness } from "./exness.js";

// Demo mode: local dev (DEV_BYPASS_EMAIL on localhost) with no API keys → empty demo account, no money moves.
// A deployed Worker never enters demo mode; without keys it reports "secrets are not configured".
const LOCAL = ["localhost", "127.0.0.1"];
const isDemo = (req, env) => !(env.EXN_API_KEY && env.EXN_API_SECRET) && !!env.DEV_BYPASS_EMAIL && LOCAL.includes(new URL(req.url).hostname);

const json = (data, status = 200) => Response.json(data, { status, headers: { "Cache-Control": "no-store" } });
const mask = (v) => (v && v.length > 16 ? `${v.slice(0, 10)}…${v.slice(-4)}` : "…");

export async function handleApi(req, env, { demo = isDemo(req, env) } = {}) {
  const url = new URL(req.url);
  const path = url.pathname.replace(/^\/api/, "");
  const method = req.method;
  // Custom header forces a CORS preflight, which we never answer — blocks cross-site writes.
  if (method !== "GET" && req.headers.get("x-studio") !== "1") return json({ detail: "Forbidden" }, 403);
  const body = method === "GET" ? null : await req.json().catch(() => ({}));
  const host = env.EXN_API_HOST || "api.exness.com";
  if (!demo && !(env.EXN_API_KEY && env.EXN_API_SECRET)) {
    const error = "Exness API is not connected. Open Settings to save and test your API credentials.";
    if (path === "/session") return json({ connected: false, demo: false, cloud: true, error, connection: { api_key: "…", host }, conditions: LABELS });
    return json({ detail: error }, 503);
  }
  const eng = new Engine(env, demo ? new DemoExness() : new Exness(env));

  if (path === "/session" && method === "GET") {
    let partner = null, error = null;
    try { partner = await eng.summary(); } catch (e) { error = String(e.message || e); }
    return json({
      connected: !!partner, demo, cloud: true, error, // signed-in email intentionally not returned
      connection: { api_key: mask(env.EXN_API_KEY), host },
      partner: partner && { uid: partner.uid, country: partner.country, clients: partner.clients_count },
      conditions: LABELS,
    });
  }
  if (path === "/overview" && method === "GET") {
    const [summary, promos, walletResult] = await Promise.all([eng.summary(), eng.list(),
      (async () => {
        try { return { wallet: await eng.wallet(), balance: await eng.balance(), warning: null }; }
        catch(e) { return {wallet: null, balance: null, warning: e instanceof ApiError
          ? `Partner Reward Wallet balance is unavailable: Exness API HTTP ${e.status} at /v1/accounts/{wallet}/balance. Your partner profile remains connected.`
          : e instanceof EngineError ? e.message : 'Partner Reward Wallet balance is temporarily unavailable.'}; }
      })()]);
    return json({
      balance: walletResult.balance, wallet: walletResult.wallet, balance_warning: walletResult.warning,
      partner_reward: Number(summary.summary_reward?.amount || 0), clients: summary.clients_count,
      // Totals count only promos shown in the list (hidden ones keep their history in D1 but don't count here).
      ...(() => { const shown = promos.filter((p) => !p.hidden); return {
        active: shown.filter((p) => p.phase === "active").length,
        spent: shown.filter((p) => p.currency !== "EXD").reduce((s, p) => s + p.spent, 0),
        spent_exd: shown.filter((p) => p.currency === "EXD").reduce((s, p) => s + p.spent, 0),
        paid: shown.reduce((s, p) => s + p.paid, 0),
        promos: shown.slice(0, 6) }; })(),
    });
  }
  if (path === "/clients" && method === "GET") {
    const [clients, accounts] = await Promise.all([eng.clients(), eng.accounts()]);
    const accs = {};
    for (const a of accounts) (accs[(a.client_uid || "").slice(0, 8)] ||= []).push({ account: a.client_account, type: a.client_account_type, platform: a.platform });
    return json(clients.map((c) => ({
      uid: c.client_uid, short: c.client_uid.slice(0, 8), reg_date: c.reg_date, country: c.client_country,
      kyc: c.kyc_passed, ftd: c.ftd_received, ftt: c.ftt_made, reward_usd: Number(c.reward_usd || 0),
      volume_lots: c.volume_lots, accounts: accs[c.client_uid.slice(0, 8)] || [],
    })));
  }
  if (path === "/promos" && method === "GET") return json((await eng.list()).filter((p) => !p.hidden));
  if (path === "/promos" && method === "POST") {
    return json(await eng.create({ title: (body.title || "").trim(), amount: body.amount, days: body.days, condition: body.condition,
      budget: body.budget, start: body.start, test: !!body.test, autoPay: body.auto_pay === true,
      audience: body.audience === "existing" ? "existing" : "new",
      currency: body.currency === "EXD" ? "EXD" : "USD" }));
  }
  const m = path.match(/^\/promos\/([\w-]+)(\/pay|\/end|\/autopay|\/metrics)?$/);
  if (m && !m[2] && method === "GET") return json(await eng.detail(m[1]));
  if (m && m[2] === "/pay" && method === "POST") {
    if (body.confirm !== true) return json({ detail: "Payout must be confirmed" }, 400);
    return json(await eng.startPayout(m[1], body.uids, body.total));
  }
  if (m && m[2] === "/metrics" && method === "GET") return json(await eng.metrics(m[1]));
  if (m && m[2] === "/end" && method === "POST") { await eng.end(m[1]); return json({ ok: true }); }
  if (m && m[2] === "/autopay" && method === "POST") {
    if (body.on === true && body.confirm !== true) return json({ detail: "Turning on automatic payouts must be confirmed" }, 400);
    await eng.setAutoPay(m[1], body.on === true); return json({ ok: true });
  }
  return json({ detail: "Not found" }, 404);
}

export default {
  async fetch(req, env) {
    try {
      await authenticate(req, env);
    } catch (e) {
      const msg = e instanceof AuthError ? e.message : "Authentication failed";
      return new Response(`403 — ${msg}`, { status: 403, headers: { "Content-Type": "text/plain; charset=utf-8" } });
    }
    const url = new URL(req.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(req);
    try {
      return await handleApi(req, env);
    } catch (e) {
      if (e instanceof EngineError) return json({ detail: e.message }, 400);
      if (e instanceof ApiError) return json({ detail: `Exness API: ${e.message}` }, 502);
      return json({ detail: String(e.message || e) }, 500);
    }
  },

};
