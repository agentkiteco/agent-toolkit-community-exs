const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num2 = (n) => Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
// cur = "USD" (Reward Wallet) or "EXD"
const money = (n, cur = "USD") => cur === "EXD" ? num2(n) + " EXD" : (Number(n) < 0 ? "−$" + num2(-n) : "$" + num2(n));
const EXD_NOTE = "EXD goes straight to the client's profile. A payout shows as Paid as soon as the API accepts the transfer.";
const fmtDate = (d) => d ? new Date(d + (d.length === 10 ? "T00:00:00" : "")).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—";
let session = null, timer = null;
const payoutsEnabled = () => session?.payouts_enabled === true;
const PAYOUTS_DISABLED = "Money transfers and automatic payouts are disabled. This promotion records qualification only.";
const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

async function api(path, opts = {}) {
  const res = await fetch("/api" + path, {
    method: opts.method || "GET",
    headers: { "Content-Type": "application/json", "X-Studio": "1" },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

function toast(msg, err = false) {
  const t = $("#toast");
  t.textContent = msg; t.className = "toast" + (err ? " err" : "");
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.add("hidden"), 4000);
}

function modal(html, wide = false) { $("#modalBox").className = "modal-box" + (wide ? " wide" : ""); $("#modalBox").innerHTML = html; $("#modal").classList.remove("hidden"); }
function closeModal() { $("#modal").classList.add("hidden"); }
$("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

const PHASE = { active: ["Active", "green"], scheduled: ["Scheduled", "blue"], completed: ["Completed", "grey"], ended: ["Ended", "grey"] };
const STATE = {
  waiting: ["Waiting", "grey"], to_pay: ["Ready to pay", "amber"], sending: ["Sending", "blue"],
  processing: ["Processing", "blue"], done: ["Paid", "green"], sent: ["Paid", "green"], failed: ["Failed", "red"], rejected: ["Rejected", "red"],
  excluded: ["Already qualified before", "grey"], missed: ["Qualified after end", "grey"],
};
const pill = ([t, c]) => `<span class="pill ${c}">${esc(t)}</span>`;
const flags = (r) => ["kyc", "ftd", "ftt"].map((k) => `<span class="flag ${r[k] ? "on" : ""}">${k.toUpperCase()}</span>`).join("");
const condShort = { ftd: "FTD", kyc: "KYC" };

/* ---------- shell ---------- */
async function loadSession() {
  session = await api("/session");
  $("#conn").innerHTML = (session.demo
    ? `<span class="dot off"></span>Test environment`
    : session.connected
    ? `<span class="dot on"></span>Exness API connected`
    : `<span class="dot off"></span>Not connected`)
    ; // signed-in email intentionally not shown
  $("#conn").style.flexWrap = "wrap";
  $("#banner").innerHTML = session.demo
    ? `<div class="banner">Test environment: create and explore promotions. No real clients or money transfers.</div>`
    : session.connected
    ? `<div class="banner">Exness API connected. Money transfers are not enabled in this version.</div>`
    : "";
}

function route() {
  clearInterval(timer);
  let [name, arg] = (location.hash.slice(1) || "overview").split("/");
  if (!session.connected && !session.demo) name = "settings";
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("active", a.dataset.route === (name === "new" || name === "promo" ? "promos" : name)));
  const views = { overview, promos, new: newPromo, promo: promoDetail, clients, settings };
  const view = $("#view");
  view.innerHTML = `<p class="muted"><span class="spin">◌</span> Loading…</p>`;
  (views[name] || overview)(view, arg).catch((e) => {
    view.innerHTML = `<div class="card"><h2>Something went wrong</h2><p class="muted">${esc(e.message)}</p>
      ${/keys are not set|connect/i.test(e.message) ? `<a class="btn primary" href="#settings">Open Settings</a>` : ""}</div>`;
  });
}
window.addEventListener("hashchange", route);

/* ---------- overview ---------- */
async function overview(view) {
  const o = await api("/overview");
  view.innerHTML = `
    <div class="head"><div><h1>Overview</h1><p class="sub">Wallet, partner reward and your client promotions.</p></div>
      <a class="btn primary" href="#new">+ Create promotion</a></div>
    <div class="grid kpis">
      ${kpi("Reward Wallet balance", o.balance == null ? "Unavailable" : money(o.balance), "available for client bonuses")}
      ${kpi("Partner reward", money(o.partner_reward), "lifetime, all clients")}
      ${kpi("Bonuses paid", money(o.spent) + (o.spent_exd ? ` <small>+ ${money(o.spent_exd, "EXD")}</small>` : ""), `${o.paid} client payouts`)}
      ${kpi("Clients", o.clients ?? "—", `${o.active} active promotion${o.active === 1 ? "" : "s"}`)}
    </div>
    ${o.balance_warning ? `<div class="banner">${esc(o.balance_warning)}</div>` : ""}
    <div class="card"><h2>Promotions</h2>${promoTable(o.promos)}</div>`;
}
const kpi = (l, v, h) => `<div class="card kpi"><div class="label">${esc(l)}</div><div class="value">${v}</div><div class="hint">${esc(h)}</div></div>`;

function promoTable(list) {
  if (!list.length) return `<div class="empty">No promotions yet.<br><br><a class="btn primary" href="#new">Create your first promotion</a></div>`;
  return `<table><thead><tr><th>Promotion</th><th>Condition</th><th>Period</th><th class="right">Bonus</th>
    <th class="right">Qualified</th><th class="right">Paid</th><th>Status</th></tr></thead><tbody>
    ${list.map((p) => `<tr class="click" onclick="location.hash='#promo/${esc(p.id)}'">
      <td><b>${esc(p.title)}</b> ${p.test ? `<span class="pill amber">TEST</span>` : ""} ${p.auto_pay ? `<span class="pill blue">AUTO</span>` : ""}</td>
      <td>${esc(p.condition_label)}</td><td>${fmtDate(p.start)} – ${fmtDate(p.end)}</td>
      <td class="right">${money(p.amount, p.currency)}</td><td class="right">${p.qualified}</td>
      <td class="right">${money(p.spent, p.currency)}${p.budget ? `<div class="muted" style="font-size:12px">of ${money(p.budget, p.currency)}</div>` : ""}</td>
      <td>${pill(PHASE[p.phase])}</td></tr>`).join("")}</tbody></table>`;
}

/* ---------- promotions ---------- */
async function promos(view) {
  const list = await api("/promos");
  let filter = "all";
  const render = () => {
    const shown = filter === "all" ? list : list.filter((p) => p.phase === filter);
    view.innerHTML = `
      <div class="head"><div><h1>Promotions</h1><p class="sub">Reward your clients for verifying their account or making their first deposit.</p></div>
        <a class="btn primary" href="#new">+ Create promotion</a></div>
      <div class="tabs">${["all", "active", "scheduled", "completed", "ended"].map((f) =>
        `<button data-f="${f}" class="${f === filter ? "on" : ""}">${f[0].toUpperCase() + f.slice(1)} (${f === "all" ? list.length : list.filter((p) => p.phase === f).length})</button>`).join("")}</div>
      <div class="card">${promoTable(shown)}</div>`;
    view.querySelectorAll(".tabs button").forEach((b) => b.onclick = () => { filter = b.dataset.f; render(); });
  };
  render();
}

/* ---------- create ---------- */
const TEMPLATES = [
  { cond: "ftd", ico: "💳", title: "First deposit bonus", desc: "Track clients who make their first deposit", step: "make their first deposit", amount: 10 },
  { cond: "kyc", ico: "🛡️", title: "Verification bonus", desc: "Track clients who pass KYC", step: "pass KYC verification", amount: 5 },
];

async function newPromo(view) {
  const todayIso = isoLocal(new Date());
  const st = { cond: "ftd", amount: 10, days: 30, budget: 500, start: todayIso, title: "", test: false, auto: false,
    audience: "new", cur: "USD" };
  view.innerHTML = `
    <div class="head"><div><h1>Create promotion</h1><p class="sub">Pick what clients need to do, the bonus, and how long the offer runs.</p></div></div>
    <div class="layout-2"><div>
      <div class="grid templates" id="tpls">${TEMPLATES.map((t) => `<button class="tpl" data-c="${t.cond}">
        <span class="ico">${t.ico}</span><b>${t.title}</b><span>${t.desc}</span></button>`).join("")}</div>
      <div class="card"><div class="grid form">
        <div class="field" style="grid-column:1/-1"><label>Promotion name</label><input id="f-title" maxlength="100"></div>
        <div class="field" style="grid-column:1/-1"><label>Bonus denomination</label>
          <div class="audience" id="f-cur">
            <button type="button" data-c="USD"><b>US dollars (USD)</b><span>Track bonuses in US dollars</span></button>
            <button type="button" data-c="EXD"><b>EXD</b><span>Track bonuses in EXD</span></button>
          </div></div>
        <div class="field"><label>Bonus per client</label><div class="prefix"><span class="cur-pfx">$</span><input id="f-amount" type="number" min="1" step="1"></div></div>
        <div class="field"><label>Total budget</label><div class="prefix"><span class="cur-pfx">$</span><input id="f-budget" type="number" min="1" step="1"></div>
          <div class="help">The total planned bonus budget.</div></div>
        <div class="field"><label>Duration</label><div class="chips" id="f-days-chips">${[7, 14, 30, 60].map((d) => `<button data-d="${d}">${d} days</button>`).join("")}</div>
          <input id="f-days" type="number" min="1" max="365"></div>
        <div class="field" style="grid-column:1/-1"><label>Who takes part</label>
          <div class="audience" id="f-aud">
            <button type="button" data-a="new"><b>New clients</b><span>Register with you during the promotion</span></button>
            <button type="button" data-a="existing"><b>Existing clients</b><span>Already registered with you before the start date</span></button>
          </div></div>
        <div class="field"><label>Start date</label><input id="f-start" type="date" min="${todayIso}">
          <div class="help" id="f-start-help"></div></div>
        <div class="field" style="grid-column:1/-1"><label style="display:flex;gap:8px;align-items:center;font-weight:500">
          <input id="f-test" type="checkbox" style="width:auto"> <span><b>Test promotion</b> — at most 1 (USD or EXD) per client and a budget of at most 10,
          start date can be in the past and clients who already met the condition are included. Use it to check qualification with a small promotion.</span></label></div>
        <div class="field" style="grid-column:1/-1"><label style="display:flex;gap:8px;align-items:center;font-weight:500">
          <input id="f-auto" type="checkbox" style="width:auto"> <span id="f-auto-txt"><b>Automatic payouts</b> — ${payoutsEnabled() ? "send bonuses to qualifying clients within the budget." : "disabled in this version."}</span></label></div>
      </div></div>
    </div>
    <div class="card summary-card" id="summary"></div></div>`;

  const set = (id, v) => ($("#" + id).value = v);
  const sync = () => {
    if (!payoutsEnabled()) st.auto = false;
    document.querySelectorAll(".tpl").forEach((b) => b.classList.toggle("on", b.dataset.c === st.cond));
    document.querySelectorAll("#f-days-chips button").forEach((b) => b.classList.toggle("on", +b.dataset.d === st.days));
    const t = TEMPLATES.find((t) => t.cond === st.cond);
    const end = new Date(st.start + "T00:00:00"); end.setDate(end.getDate() + (st.days || 1) - 1);
    const endIso = isoLocal(end);
    const M = (n) => money(n, st.cur), exd = st.cur === "EXD";
    const title = st.title || `${st.test ? "TEST · " : ""}${exd ? `${st.amount} EXD` : `$${st.amount}`} ${t.title.toLowerCase()} · ${st.days} days`;
    const endOk = endIso >= todayIso;
    const max = st.budget && st.amount ? Math.floor(st.budget / st.amount) : null;
    const valid = st.amount > 0 && st.days >= 1 && st.days <= 365 && (!st.budget || st.budget >= st.amount) && (!st.auto || st.budget)
      && (st.test ? st.amount <= 1 && st.budget && st.budget <= 10 && endOk : st.start >= todayIso);
    $("#summary").innerHTML = `
      <div class="muted" style="font-size:13px;font-weight:600">SUMMARY</div>
      <div class="big">${M(st.amount)} for ${condShort[st.cond]} ${st.test ? `<span class="pill amber">TEST</span>` : ""} ${st.auto ? `<span class="pill blue">AUTO</span>` : ""}</div>
      <ul>
        <li>${st.audience === "existing"
          ? `Every <b>existing client</b> (registered with you before <b>${fmtDate(st.start)}</b>), from <b>${fmtDate(st.start)}</b> to <b>${fmtDate(endIso)}</b>`
          : `Every new client who <b>registers with you</b> from <b>${fmtDate(st.start)}</b> to <b>${fmtDate(endIso)}</b>`}</li>
        <li>and <b>${esc(t.step)}</b> in that period</li>
        <li>${payoutsEnabled() ? "Receive" : "Planned bonus:"} <b>${M(st.amount)}</b>${payoutsEnabled() ? (exd ? " to their profile from your EXD balance" : " from your Reward Wallet") : "; transfers disabled"}</li>
        <li>${max ? `Budget ${M(st.budget)} = up to <b>${max}</b> clients` : "No budget limit"}</li>
      </ul>
      <div class="note">${st.test
        ? `Test mode: clients who already met the condition are included, to check qualification. Limits: ${M(1)} per client, ${M(10)} budget.${endOk ? "" : " <b>The period must include today.</b>"}`
        : "Clients who already met the condition before the start are not eligible."}
        ${exd && payoutsEnabled() ? `<br>${EXD_NOTE}` : ""}
        <br>${!payoutsEnabled() ? PAYOUTS_DISABLED : st.auto ? (st.budget ? `Payouts are sent <b>automatically</b> (checked every ~10 min), without your confirmation — only to new qualifiers, never above the budget.` : "<b>Automatic payouts need a budget.</b>") : "You review and confirm every payout."}</div>
      <button class="btn primary" id="go" style="width:100%" ${valid ? "" : "disabled"}>Launch promotion</button>`;
    view.querySelectorAll("#f-aud button").forEach((b) => b.classList.toggle("on", b.dataset.a === st.audience));
    view.querySelectorAll("#f-cur button").forEach((b) => b.classList.toggle("on", b.dataset.c === st.cur));
    view.querySelectorAll(".cur-pfx").forEach((x) => { x.textContent = exd ? "EXD" : "$"; x.parentElement.classList.toggle("wide", exd); });
    $("#f-auto").disabled = exd || !payoutsEnabled();
    $("#f-auto-txt").style.opacity = exd || !payoutsEnabled() ? 0.5 : 1;
    $("#f-start-help").textContent = st.audience === "existing"
      ? "Clients registered before this date take part; only what they do from this date counts."
      : "Clients who register with you from this date take part.";
    $("#go").onclick = () => confirmLaunch({ ...st, title, end: endIso });
  };
  set("f-amount", st.amount); set("f-budget", st.budget); set("f-days", st.days); set("f-start", st.start);
  view.querySelectorAll("#f-aud button").forEach((b) => b.onclick = () => { st.audience = b.dataset.a; sync(); });
  // EXD: no automatic payouts (the API has no EXD transfer status yet)
  view.querySelectorAll("#f-cur button").forEach((b) => b.onclick = () => {
    st.cur = b.dataset.c; if (st.cur === "EXD") { st.auto = false; $("#f-auto").checked = false; } sync();
  });
  view.querySelectorAll(".tpl").forEach((b) => b.onclick = () => {
    st.cond = b.dataset.c; st.amount = TEMPLATES.find((t) => t.cond === st.cond).amount; set("f-amount", st.amount); sync();
  });
  view.querySelectorAll("#f-days-chips button").forEach((b) => b.onclick = () => { st.days = +b.dataset.d; set("f-days", st.days); sync(); });
  $("#f-title").oninput = (e) => { st.title = e.target.value.trim(); sync(); };
  $("#f-amount").oninput = (e) => { st.amount = +e.target.value; sync(); };
  $("#f-budget").oninput = (e) => { st.budget = +e.target.value || null; sync(); };
  $("#f-days").oninput = (e) => { st.days = +e.target.value; sync(); };
  $("#f-start").oninput = (e) => { st.start = e.target.value || todayIso; sync(); };
  $("#f-auto").onchange = (e) => { st.auto = payoutsEnabled() && e.target.checked; sync(); };
  $("#f-test").onchange = (e) => {
    st.test = e.target.checked;
    if (st.test) { st.amount = 1; st.budget = 5; } else { st.amount = 10; st.budget = 500; if (st.start < todayIso) st.start = todayIso; }
    $("#f-start").min = st.test ? "" : todayIso;
    $("#f-amount").max = st.test ? 1 : "";
    set("f-amount", st.amount); set("f-budget", st.budget); set("f-start", st.start); sync();
  };
  sync();
}

function confirmLaunch(p) {
  if (!payoutsEnabled()) p.auto = false;
  modal(`<h3>Launch this promotion?</h3>
    <p><b>${esc(p.title)}</b></p>
    <p class="muted">${money(p.amount, p.cur)} per client for ${condShort[p.cond]} · ${fmtDate(p.start)} – ${fmtDate(p.end)} · budget ${p.budget ? money(p.budget, p.cur) : "none"}</p>
    ${p.cur === "EXD" && payoutsEnabled() ? `<p class="muted">Paid in <b>EXD</b>. ${EXD_NOTE}</p>` : ""}
    <p class="muted">${p.audience === "existing"
      ? `Applies to every client already registered with you before ${fmtDate(p.start)}.`
      : "Applies to every client who registers with you in this period — no special link needed."}</p>
    ${p.test ? `<p><span class="pill amber">TEST</span> Clients who already met the condition are included.</p>` : ""}
    ${!payoutsEnabled() ? `<p class="muted">${PAYOUTS_DISABLED}</p>` : p.auto ? `<p style="color:var(--red);font-weight:600"><span class="pill blue">AUTO</span> Bonuses will be sent automatically without confirmation, up to ${money(p.budget)} in total. Transfers can't be reversed.</p>`
      : `<p class="muted">No money is sent now — you confirm payouts later.</p>`}
    <div class="actions"><button class="btn" onclick="closeModal()">Cancel</button><button class="btn primary" id="launch">Launch</button></div>`);
  $("#launch").onclick = async (e) => {
    e.target.disabled = true;
    try {
      const r = await api("/promos", { method: "POST", body: { title: p.title, amount: p.amount, days: p.days, condition: p.cond,
        budget: p.budget, start: p.start, test: p.test, auto_pay: payoutsEnabled() && !!p.auto, audience: p.audience, currency: p.cur } });
      closeModal(); toast("Promotion launched"); location.hash = "#promo/" + r.id;
    } catch (err) { closeModal(); toast(err.message, true); }
  };
}

/* ---------- promo metrics charts ---------- */
const fmtNum = (v, d) => Number(v || 0).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const MX = {
  lots: { label: "Volume, lots", title: "Daily trading volume, lots", fmt: (v) => fmtNum(v, 2) + " lots" },
  mln: { label: "Volume, $M", title: "Daily trading volume, $ million", fmt: (v) => "$" + fmtNum(v, 3) + "M" },
  orders: { label: "Orders", title: "Daily orders", fmt: (v) => fmtNum(v, 0) + " orders" },
  reward: { label: "Partner reward", title: "Daily partner reward", fmt: (v) => money(v) },
  bonus: { label: "Bonuses paid", title: "Daily bonuses paid by you", fmt: (v) => money(v, bonusCur) },
};
let bonusCur = "USD"; // currency of the promo whose charts are shown
const shortDate = (iso) => new Date(iso + "T00:00:00Z").toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const niceMax = (v) => { if (!(v > 0)) return 1; const e = 10 ** Math.floor(Math.log10(v)); const f = v / e; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * e; };
const axisFmt = (v) => v >= 1000 ? fmtNum(v / 1000, v >= 10000 ? 0 : 1) + "k" : fmtNum(v, v < 10 && v % 1 ? (v < 1 ? 2 : 1) : 0);

function metricsHtml(mx, tab) {
  const t = mx.totals, roi = t.bonus ? t.reward / t.bonus : null;
  return `<div class="toolbar"><h2 style="margin:0">Performance during the promotion</h2>
      <div class="chips" id="mxTabs" style="margin:0">${Object.entries(MX).map(([k, m]) => `<button data-k="${k}" class="${k === tab ? "on" : ""}">${m.label}</button>`).join("")}</div></div>
    <div class="grid mx-kpis">
      <div><div class="label">Trading volume</div><div class="value">${fmtNum(t.lots, 2)} <small>lots</small></div><div class="hint">$${fmtNum(t.mln, 2)}M notional</div></div>
      <div><div class="label">Orders</div><div class="value">${fmtNum(t.orders, 0)}</div><div class="hint">${t.traders} of ${t.participants} clients traded</div></div>
      <div><div class="label">Partner reward</div><div class="value">${money(t.reward)}</div><div class="hint">earned from participants in the period</div></div>
      <div><div class="label">Bonuses paid</div><div class="value">${money(t.bonus, bonusCur)}</div><div class="hint">${roi !== null ? `reward is <b>${fmtNum(roi, 1)}×</b> the bonuses${bonusCur === "EXD" ? " (1 EXD = $1)" : ""}` : "nothing paid yet"}</div></div>
    </div>
    ${mx.days.length ? `<div class="chart-title">${MX[tab].title}</div><div class="chart" id="chartBars"></div>
    <div class="chart-title">Partner reward vs bonuses paid, cumulative
      <span class="legend"><span><i style="background:var(--s1)"></i>Partner reward</span><span><i style="background:var(--s2)"></i>Bonuses paid</span></span></div>
    <div class="chart" id="chartLines"></div>
    ${symbolsHtml(mx.symbols || [])}` : `<p class="muted">The promotion hasn't started yet.</p>`}
    <p class="muted" style="font-size:12px;margin:10px 0 0">Trading data from the API partner reports (per client, per day, UTC) for this promotion's participants. Today's figures are still filling in.</p>`;
}

function tipShow(ev, html) {
  let t = $("#tip");
  if (!t) { t = document.createElement("div"); t.id = "tip"; t.className = "tip"; document.body.appendChild(t); }
  t.innerHTML = html; t.style.display = "block";
  const w = t.offsetWidth, x = ev.clientX + 14 + w > innerWidth ? ev.clientX - w - 14 : ev.clientX + 14;
  t.style.left = x + "px"; t.style.top = Math.max(8, ev.clientY - 40) + "px";
}
const tipHide = () => { const t = $("#tip"); if (t) t.style.display = "none"; };
addEventListener("scroll", tipHide, { passive: true, capture: true });

// Symbols participants traded in the promo period — horizontal bars by lots, top 12 + "Other".
function symbolsHtml(list) {
  if (!list.length) return `<div class="chart-title">Traded symbols</div><p class="muted" style="font-size:13px;margin:0">No trades by participants in the promotion period yet.</p>`;
  const top = list.slice(0, 12), rest = list.slice(12);
  if (rest.length) top.push({ symbol: `Other (${rest.length})`, other: true, lots: Math.round(rest.reduce((a, s) => a + s.lots, 0) * 100) / 100,
    orders: rest.reduce((a, s) => a + s.orders, 0), clients: null, names: rest.map((s) => s.symbol).join(", ") });
  const max = Math.max(...top.map((s) => s.lots), 0.01);
  return `<div class="chart-title">Traded symbols, lots · ${list.length} symbol${list.length === 1 ? "" : "s"}</div>
    <div class="syms">${top.map((s, i) => `<div class="sym-row" data-i="${i}"><span class="sym-name">${esc(s.symbol)}</span>
      <span class="sym-track"><span class="sym-bar" style="width:${Math.max(0.5, (s.lots / max) * 100)}%;background:var(--s1)"></span></span>
      <span class="sym-val">${fmtNum(s.lots, 2)}</span></div>`).join("")}</div>`;
}
function bindSymbols(el, list) {
  if (!el) return;
  const top = list.slice(0, 12), rest = list.slice(12);
  el.querySelectorAll(".sym-row").forEach((r) => {
    const i = +r.dataset.i, s = top[i];
    r.onmousemove = (ev) => tipShow(ev, s ? `<b>${esc(s.symbol)}</b>${s.group ? ` · ${esc(s.group[0].toUpperCase() + s.group.slice(1))}` : ""}<br>${fmtNum(s.lots, 2)} lots · ${fmtNum(s.orders, 0)} orders<br>${s.clients} client${s.clients === 1 ? "" : "s"}`
      : `<b>Other symbols</b><br>${fmtNum(rest.reduce((a, x) => a + x.lots, 0), 2)} lots · ${fmtNum(rest.reduce((a, x) => a + x.orders, 0), 0)} orders<br><span class="muted">${esc(rest.map((x) => x.symbol).join(", "))}</span>`);
    r.onmouseleave = tipHide;
  });
}
function chartFrame(el, days, max, H) {
  const W = Math.max(320, el.clientWidth), L = 48, R = 16, T = 12, B = 26;
  const n = days.length, step = (W - L - R) / n;
  const y = (v) => T + (H - T - B) * (1 - v / max);
  const xc = (i) => L + step * i + step / 2;
  let g = "";
  for (const f of [0, 0.5, 1]) {
    const v = max * f;
    g += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="${f ? "var(--line)" : "#c9c8c2"}" stroke-width="1"/>
      <text x="${L - 8}" y="${y(v) + 4}" text-anchor="end" class="ax">${axisFmt(v)}</text>`;
  }
  const every = Math.max(1, Math.ceil(n / Math.floor((W - L - R) / 64)));
  days.forEach((d, i) => { if (i % every === 0) g += `<text x="${xc(i)}" y="${H - 8}" text-anchor="middle" class="ax">${shortDate(d.date)}</text>`; });
  return { W, H, L, R, T, B, n, step, y, xc, g };
}

function drawBars(el, days, key) {
  if (!el) return;
  const m = MX[key], max = niceMax(Math.max(0, ...days.map((d) => d[key])));
  const f = chartFrame(el, days, max, 200);
  const bw = Math.max(2, Math.min(32, f.step - 2));
  let bars = "", hits = "";
  days.forEach((d, i) => {
    const v = d[key], x = f.xc(i) - bw / 2, top = f.y(v), base = f.y(0), h = base - top;
    if (v > 0) {
      const r = Math.min(4, bw / 2, h);
      bars += `<path d="M${x},${base} V${top + r} Q${x},${top} ${x + r},${top} H${x + bw - r} Q${x + bw},${top} ${x + bw},${top + r} V${base} Z" fill="var(${key === "bonus" ? "--s2" : "--s1"})" data-i="${i}"/>`;
    }
    hits += `<rect x="${f.L + f.step * i}" y="${f.T}" width="${f.step}" height="${f.H - f.T - f.B}" fill="transparent" data-i="${i}"/>`;
  });
  el.innerHTML = `<svg width="${f.W}" height="${f.H}" role="img" aria-label="${esc(m.title)}">${f.g}${bars}${hits}</svg>`;
  el.querySelectorAll("rect[data-i]").forEach((r) => {
    const i = +r.dataset.i, d = days[i];
    r.onmousemove = (ev) => {
      el.querySelectorAll("path[data-i]").forEach((p) => p.style.opacity = +p.dataset.i === i ? 1 : 0.45);
      tipShow(ev, `<b>${shortDate(d.date)}</b><br>${m.fmt(d[key])}`);
    };
    r.onmouseleave = () => { el.querySelectorAll("path[data-i]").forEach((p) => p.style.opacity = 1); tipHide(); };
  });
}

function drawLines(el, days) {
  if (!el) return;
  let a = 0, b = 0;
  const cum = days.map((d) => ({ date: d.date, reward: (a += d.reward), bonus: (b += d.bonus) }));
  const max = niceMax(Math.max(0, ...cum.map((c) => Math.max(c.reward, c.bonus))));
  const f = chartFrame(el, days, max, 200);
  const line = (k) => cum.map((c, i) => `${i ? "L" : "M"}${f.xc(i)},${f.y(c[k])}`).join(" ");
  const last = cum[cum.length - 1], li = cum.length - 1;
  const lbl = (k, color) => `<circle cx="${f.xc(li)}" cy="${f.y(last[k])}" r="4" fill="${color}" stroke="#fff" stroke-width="2"/>`;
  const hits = cum.map((c, i) => `<rect x="${f.L + f.step * i}" y="${f.T}" width="${f.step}" height="${f.H - f.T - f.B}" fill="transparent" data-i="${i}"/>`).join("");
  el.innerHTML = `<svg width="${f.W}" height="${f.H}" role="img" aria-label="Cumulative partner reward and bonuses paid">${f.g}
    <path d="${line("bonus")}" fill="none" stroke="var(--s2)" stroke-width="2" stroke-linejoin="round"/>
    <path d="${line("reward")}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>
    ${lbl("bonus", "var(--s2)")}${lbl("reward", "var(--s1)")}
    <line id="xh" x1="0" x2="0" y1="${f.T}" y2="${f.H - f.B}" stroke="#9a9993" stroke-width="1" style="display:none"/>
    <circle id="xh1" r="4" fill="var(--s1)" stroke="#fff" stroke-width="2" style="display:none"/>
    <circle id="xh2" r="4" fill="var(--s2)" stroke="#fff" stroke-width="2" style="display:none"/>${hits}</svg>`;
  const xh = el.querySelector("#xh"), c1 = el.querySelector("#xh1"), c2 = el.querySelector("#xh2");
  el.querySelectorAll("rect[data-i]").forEach((r) => {
    const i = +r.dataset.i, c = cum[i], x = f.xc(i);
    r.onmousemove = (ev) => {
      xh.setAttribute("x1", x); xh.setAttribute("x2", x); xh.style.display = "";
      c1.setAttribute("cx", x); c1.setAttribute("cy", f.y(c.reward)); c1.style.display = "";
      c2.setAttribute("cx", x); c2.setAttribute("cy", f.y(c.bonus)); c2.style.display = "";
      tipShow(ev, `<b>${shortDate(c.date)}</b> · since start<br><i class="sw" style="background:var(--s1)"></i>Partner reward ${money(c.reward)}
        <br><i class="sw" style="background:var(--s2)"></i>Bonuses paid ${money(c.bonus, bonusCur)}<br><span class="muted">Net ${money(c.reward - c.bonus)}</span>`);
    };
    r.onmouseleave = () => { xh.style.display = c1.style.display = c2.style.display = "none"; tipHide(); };
  });
}

/* ---------- promo detail ---------- */
async function promoDetail(view, id) {
  const selected = new Set();
  let d, mx = null, mxErr = null, mxTab = "lots";
  // Background refresh: redraw only when something actually changed (otherwise just update "Last checked").
  const sig = (x) => JSON.stringify({ ...x, last_scan: null });
  const load = async () => {
    const nd = await api("/promos/" + encodeURIComponent(id));
    const same = d && sig(nd) === sig(d);
    d = nd;
    if (same && $("#lastChk")) $("#lastChk").textContent = d.last_scan ? new Date(d.last_scan).toLocaleTimeString() : "—";
    else render();
  };
  const loadMx = async () => {
    try { mx = await api(`/promos/${encodeURIComponent(id)}/metrics`); mxErr = null; } catch (e) { mxErr = e.message; }
    if (d) render();
  };
  const render = () => {
    const s = d.stats;
    const payable = d.participants.filter((r) => ["to_pay", "failed", "rejected"].includes(r.state) && !r.blocked);
    [...selected].forEach((u) => { if (!payable.some((r) => r.uid === u)) selected.delete(u); });
    const total = selected.size * d.amount;
    const cur = d.currency || "USD", M = (n) => money(n, cur), exd = cur === "EXD";
    bonusCur = cur;
    const used = d.budget ? Math.min(100, ((s.spent + s.in_flight_amount) / d.budget) * 100) : 0;
    const keepY = window.scrollY; // keep the scroll position across redraws
    view.innerHTML = `
      <div class="head"><div><a href="#promos" class="muted" style="text-decoration:none">← Promotions</a>
        <h1 style="margin-top:6px">${esc(d.title)} ${pill(PHASE[d.phase])} ${d.test ? `<span class="pill amber">TEST</span>` : ""} ${d.auto_pay ? `<span class="pill blue">AUTO-PAY</span>` : ""}</h1>
        <p class="sub">${M(d.amount)} for ${esc(d.condition_label)} · ${d.audience === "existing"
          ? `existing clients (registered before ${fmtDate(d.start)}) · ${fmtDate(d.start)} – ${fmtDate(d.end)}`
          : `new clients from ${fmtDate(d.start)} to ${fmtDate(d.end)}`}</p></div>
        <div style="display:flex;gap:8px"><button class="btn" id="refresh">↻ Refresh</button>
        ${payoutsEnabled() && d.auto_pay ? `<button class="btn" id="autoBtn">Turn off auto-pay</button>` : payoutsEnabled() && d.phase !== "ended" && d.budget && !exd ? `<button class="btn" id="autoBtn">Turn on auto-pay</button>` : ""}
        ${d.phase !== "ended" ? `<button class="btn danger" id="endBtn">End promotion</button>` : ""}</div></div>
      ${exd && payoutsEnabled() ? `<div class="note" style="margin-bottom:14px"><b>Paid in EXD.</b> ${EXD_NOTE}</div>` : ""}
      ${!payoutsEnabled() ? `<div class="note" style="margin-bottom:14px">${PAYOUTS_DISABLED}</div>` : d.auto_pay ? `<div class="note" style="margin-bottom:14px"><b>Automatic payouts are on.</b> New qualifiers are paid within ~10 minutes, up to the budget.${d.auto_note ? `<br><span style="color:var(--red)">${esc(d.auto_note)}</span>` : ""}</div>` : ""}
      <div class="grid kpis">
        ${d.audience === "existing" ? kpi("Existing clients", s.participants, `registered before ${fmtDate(d.start)}`) : kpi("New clients", s.participants, "registered in the period")}
        ${kpi("Qualified", s.qualified, `${s.to_pay} ready to pay`)}
        ${kpi("Paid", M(s.spent), `${s.paid} clients${s.in_flight ? ` · ${s.in_flight} in progress` : ""}`).replace("</div></div>", d.budget ? `</div><div class="progress"><div style="width:${used}%"></div></div><div class="hint">${M(d.budget - s.spent - s.in_flight_amount)} of ${M(d.budget)} budget left</div></div>` : "</div></div>")}
        ${kpi("Partner reward", money(s.earned), `lifetime, from participants · net ${money(s.net)}`)}
      </div>
      <div class="card" id="mx">${mx ? metricsHtml(mx, mxTab) : mxErr
        ? `<h2>Performance during the promotion</h2><p class="muted">Couldn't load trading data: ${esc(mxErr)}</p>`
        : `<h2>Performance during the promotion</h2><p class="muted"><span class="spin">◌</span> Loading trading data…</p>`}</div>
      <div class="card">
        <div class="toolbar"><h2 style="margin:0">Clients</h2>
          <div style="display:flex;gap:10px;align-items:center">
            ${d.paying ? `<span class="muted"><span class="spin">◌</span> Sending payouts…</span>` : ""}
            <button class="btn primary" id="payBtn" ${payoutsEnabled() && selected.size && !d.paying ? "" : "disabled"}>${payoutsEnabled() ? "Pay selected" : "Payouts disabled"}${selected.size ? ` (${M(total)})` : ""}</button></div></div>
        ${d.participants.length ? `<table><thead><tr>
          <th style="width:28px"><input type="checkbox" id="all" ${payable.length && selected.size === payable.length ? "checked" : ""} ${payable.length ? "" : "disabled"}></th>
          <th>Client</th><th>Registered</th><th>Country</th><th>Progress</th><th>Account</th><th>Status</th><th class="right">Volume, lots</th><th class="right">Reward</th><th class="right">Bonus</th></tr></thead><tbody>
          ${d.participants.map((r) => {
            const can = payable.includes(r);
            return `<tr><td>${can ? `<input type="checkbox" data-u="${esc(r.uid)}" ${selected.has(r.uid) ? "checked" : ""}>` : ""}</td>
              <td class="mono">${esc(r.short)}</td><td>${fmtDate(r.reg_date)}</td><td>${esc(r.country)}</td><td>${flags(r)}</td>
              <td class="mono">${exd ? (r.account ? "Client profile" : "—") : esc(r.account || "—")}</td>
              <td>${pill(STATE[r.state] || [r.state, "grey"])}${r.blocked ? `<div class="muted" style="font-size:12px">${esc(r.blocked)}</div>` : ""}
                ${r.error ? `<div style="font-size:12px;color:var(--red)">${esc(r.error)}</div>` : ""}</td>
              <td class="right">${mx ? fmtNum(mx.per_client[r.uid]?.lots || 0, 1) : "…"}</td>
              <td class="right">${mx ? money(mx.per_client[r.uid]?.reward || 0) : "…"}</td>
              <td class="right">${["done", "sent", "processing", "sending"].includes(r.state) || can ? M(d.amount) : "—"}</td></tr>`;
          }).join("")}</tbody></table>`
          : `<div class="empty">${d.audience === "existing" ? "No clients registered before the start date." : "No clients have registered in this period yet."}${d.phase === "scheduled" ? " The promotion hasn't started." : ""}</div>`}
        <p class="muted" style="font-size:12px;margin:14px 0 0">Last checked <span id="lastChk">${d.last_scan ? new Date(d.last_scan).toLocaleTimeString() : "—"}</span>.
          Qualification is recorded the first time the app sees it, so keep the app running (or open it daily) while the promotion is active.</p>
      </div>`;
    $("#refresh").onclick = () => { load().catch((e) => toast(e.message, true)); loadMx(); };
    if (mx) {
      view.querySelectorAll("#mxTabs button").forEach((b) => b.onclick = () => { mxTab = b.dataset.k; render(); });
      const draw = () => { drawBars($("#chartBars"), mx.days, mxTab); drawLines($("#chartLines"), mx.days); };
      requestAnimationFrame(draw);
      bindSymbols($(".syms"), mx.symbols || []);
      window.onresize = () => { if ($("#chartBars")) draw(); };
    }
    $("#endBtn") && ($("#endBtn").onclick = () => confirmEnd(d, load));
    $("#autoBtn") && ($("#autoBtn").onclick = () => confirmAuto(d, load));
    // Selection updates only the checkboxes and the Pay button — no full re-render, so the page doesn't jump.
    const syncSel = () => {
      const n = selected.size, btn = $("#payBtn");
      btn.disabled = !payoutsEnabled() || !n || !!d.paying;
      btn.textContent = payoutsEnabled() ? `Pay selected${n ? ` (${money(n * d.amount, d.currency)})` : ""}` : "Payouts disabled";
      if ($("#all")) $("#all").checked = !!payable.length && n === payable.length;
      view.querySelectorAll("input[data-u]").forEach((c) => (c.checked = selected.has(c.dataset.u)));
    };
    $("#all") && ($("#all").onchange = (e) => { payable.forEach((r) => e.target.checked ? selected.add(r.uid) : selected.delete(r.uid)); syncSel(); });
    view.querySelectorAll("input[data-u]").forEach((c) => c.onchange = () => { c.checked ? selected.add(c.dataset.u) : selected.delete(c.dataset.u); syncSel(); });
    $("#payBtn").onclick = () => confirmPay(d, [...selected], load);
    window.scrollTo(0, keepY);
  };
  await load();
  loadMx();
  timer = setInterval(() => { if (!$("#modal").classList.contains("hidden")) return; load().catch(() => {}); }, 15000);
}

function confirmPay(d, uids, reload) {
  if (!payoutsEnabled()) return toast(PAYOUTS_DISABLED, true);
  const total = uids.length * d.amount, cur = d.currency || "USD", M = (n) => money(n, cur);
  modal(`<h3>Send ${uids.length} payout${uids.length > 1 ? "s" : ""}?</h3>
    <div class="total">${M(total)}</div>
    <p class="muted">${uids.length} × ${M(d.amount)} ${cur === "EXD"
      ? "in EXD from your EXD balance, to each client's profile."
      : `from Reward Wallet <span class="mono">${esc(d.wallet)}</span>.`}</p>
    <p style="color:var(--red);font-weight:600">${cur === "EXD" ? "Real EXD." : "Real money."} Transfers can't be cancelled or reversed.</p>
    <div class="actions"><button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn primary" id="doPay">Send ${M(total)}</button></div>`);
  $("#doPay").onclick = async (e) => {
    e.target.disabled = true;
    try {
      await api(`/promos/${encodeURIComponent(d.id)}/pay`, { method: "POST", body: { uids, total, confirm: true } });
      closeModal(); toast("Payouts started — statuses update automatically"); reload();
    } catch (err) { closeModal(); toast(err.message, true); reload(); }
  };
}

function confirmAuto(d, reload) {
  if (!payoutsEnabled()) return toast(PAYOUTS_DISABLED, true);
  const on = !d.auto_pay;
  modal((on ? `<h3>Turn on automatic payouts?</h3>
      <p>Every new qualifier gets ${money(d.amount)} automatically, without confirmation, until the ${money(d.budget)} budget is used.</p>
      <p style="color:var(--red);font-weight:600">Real money. Transfers can't be cancelled or reversed.</p>`
    : `<h3>Turn off automatic payouts?</h3><p class="muted">Payouts already started will finish. New qualifiers will wait for your confirmation.</p>`)
    + `<div class="actions"><button class="btn" onclick="closeModal()">Cancel</button><button class="btn primary" id="doAuto">${on ? "Turn on" : "Turn off"}</button></div>`);
  $("#doAuto").onclick = async (e) => {
    e.target.disabled = true;
    try { await api(`/promos/${encodeURIComponent(d.id)}/autopay`, { method: "POST", body: { on, confirm: on } }); closeModal(); toast(on ? "Automatic payouts on" : "Automatic payouts off"); reload(); }
    catch (err) { closeModal(); toast(err.message, true); }
  };
}

function confirmEnd(d, reload) {
  modal(`<h3>End “${esc(d.title)}”?</h3>
    <p class="muted">New qualifiers won't be recorded. ${payoutsEnabled() ? "Clients already qualified can still be paid." : PAYOUTS_DISABLED}</p>
    <div class="actions"><button class="btn" onclick="closeModal()">Cancel</button><button class="btn primary" id="doEnd">End promotion</button></div>`);
  $("#doEnd").onclick = async () => {
    try { await api(`/promos/${encodeURIComponent(d.id)}/end`, { method: "POST", body: {} }); closeModal(); toast("Promotion ended"); reload(); }
    catch (err) { closeModal(); toast(err.message, true); }
  };
}

/* ---------- clients ---------- */
async function clients(view) {
  const list = await api("/clients");
  let q = "";
  const render = () => {
    const shown = list.filter((c) => !q || c.uid.includes(q) || c.accounts.some((a) => a.account.includes(q)) || (c.country || "").toLowerCase() === q);
    $("#rows").innerHTML = shown.length ? shown.map((c) => `<tr><td class="mono">${esc(c.short)}</td><td>${fmtDate(c.reg_date)}</td><td>${esc(c.country)}</td>
      <td>${flags(c)}</td><td class="mono">${c.accounts.map((a) => esc(a.account)).join("<br>") || "—"}</td>
      <td class="right">${c.volume_lots ?? "—"}</td><td class="right">${money(c.reward_usd)}</td></tr>`).join("")
      : `<tr><td colspan="7" class="empty">No clients match.</td></tr>`;
  };
  view.innerHTML = `<div class="head"><div><h1>Clients</h1><p class="sub">Your referred clients, their progress and the reward they bring.</p></div></div>
    <div class="card"><div class="toolbar"><input id="q" placeholder="Search by client ID, account or country" style="flex:1;max-width:380px;border:1px solid var(--line);border-radius:9px;padding:9px 12px">
      <span class="muted">${list.length} clients</span></div>
      <table><thead><tr><th>Client</th><th>Registered</th><th>Country</th><th>Progress</th><th>Accounts</th><th class="right">Volume, lots</th><th class="right">Partner reward</th></tr></thead>
      <tbody id="rows"></tbody></table></div>`;
  $("#q").oninput = (e) => { q = e.target.value.trim().toLowerCase(); render(); };
  render();
}

/* ---------- settings / connect ---------- */
async function settings(view) {
  await loadSession();
  view.innerHTML = `<div class="head"><div><h1>Settings</h1><p class="sub">Connect your Exness partner account.</p></div></div>
    <div class="card connect"><h2>Exness API ${session.connected && !session.demo ? '<span class="pill green">Connected</span>' : '<span class="pill amber">Not connected</span>'}</h2>
    ${!session.demo ? `<p class="muted">Saved API key: <span class="mono">${esc(session.connection.api_key)}</span></p>` : ''}
    <p class="muted">Enter your API key and secret. The connection is verified before saving. Credentials are encrypted on the server and are never returned to the browser.</p>
    <form id="credentials-form" autocomplete="off">
    <label style="display:block;margin:20px 0 8px" for="api-key">API key</label><input id="api-key" type="password" required autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:12px" placeholder="Exness API key">
    <label style="display:block;margin:20px 0 8px" for="api-secret">API secret</label><input id="api-secret" type="password" required autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:12px" placeholder="128 hexadecimal characters" pattern="[A-Fa-f0-9]{128}">
    <p class="muted">The key needs partner report permissions and no IP allowlist. Money transfers are not enabled in this version.</p>
    <p id="connection-result" role="status"></p><button class="btn primary" type="submit">Save and test connection</button></form></div>`;
  $('#credentials-form').onsubmit=async e=>{
    e.preventDefault(); const button=e.target.querySelector('button');button.disabled=true;
    $('#connection-result').textContent='Checking connection…';
    try {
      await api('/settings/credentials',{method:'POST',body:{api_key:$('#api-key').value,api_secret:$('#api-secret').value}});
      $('#api-key').value='';$('#api-secret').value='';
      await settings(view);$('#connection-result').textContent='Connected. Credentials saved securely.';toast('Exness API connected');
    } catch(error){$('#api-secret').value='';$('#connection-result').textContent=error.message;}
    finally{button.disabled=false;}
  };
}

loadSession().then(route).catch((e) => toast(e.message, true));
