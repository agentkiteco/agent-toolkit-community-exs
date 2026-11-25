// Signed Exness API client for Workers (Ed25519, sign_version 1).

export class ApiError extends Error {
  constructor(status, payload) {
    const code = payload && (payload.error_message || payload.code);
    const msg = payload && (payload.description || payload.message);
    super(`HTTP ${status} ${code || ""} ${msg || ""}`.trim());
    this.status = status;
    this.code = code ? String(code) : null;
    this.payload = payload;
  }
}

const enc = new TextEncoder();
export const b64u = (bytes) =>
  btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const hexToBytes = (hex) => new Uint8Array(hex.trim().match(/../g).map((h) => parseInt(h, 16)));

let cachedKey = null, cachedFor = null;
async function signingKey(secretHex) {
  if (cachedKey && cachedFor === secretHex) return cachedKey;
  const raw = hexToBytes(secretHex); // 32-byte seed + 32-byte public key
  if (raw.length !== 64) throw new Error("EXN_API_SECRET must be 128 hex characters");
  const jwk = { kty: "OKP", crv: "Ed25519", d: b64u(raw.slice(0, 32)), x: b64u(raw.slice(32)) };
  cachedKey = await crypto.subtle.importKey("jwk", jwk, { name: "Ed25519" }, false, ["sign"]);
  cachedFor = secretHex;
  return cachedKey;
}

export class Exness {
  constructor(env) {
    if (!env.EXN_API_KEY || !env.EXN_API_SECRET) throw new Error("Exness API secrets are not configured");
    this.env = env;
    this.host = "api.exness.com";
  }

  // Reads are retried once on a transient API error (e.g. a one-off 403 "invalid token", 5xx).
  // Writes (transfers) are never retried here — the payout engine handles them with idempotency keys.
  async call(method, path, body = null, idem = null) {
    if (method !== "GET") throw new Error("This API client only supports read requests");
    try { return await this.send(method, path, body, idem); }
    catch (e) {
      if (method !== "GET" || !(e.status === 403 || e.status === 429 || e.status >= 500)) throw e;
      await new Promise((r) => setTimeout(r, 700));
      return this.send(method, path, body, idem);
    }
  }

  async send(method, path, body = null, idem = null) {
    if (method !== "GET") throw new Error("This API client only supports read requests");
    const bodyBytes = enc.encode(body ? JSON.stringify(body) : "");
    idem = method === "GET" ? "" : idem || crypto.randomUUID();
    const ts = Date.now();
    const data = enc.encode(JSON.stringify({
      api_key: this.env.EXN_API_KEY, idempotency_key: idem, timestamp: ts, sign_version: 1, method, path,
      body_hash: b64u(await crypto.subtle.digest("SHA-256", bodyBytes)),
    }));
    const sig = await crypto.subtle.sign({ name: "Ed25519" }, await signingKey(this.env.EXN_API_SECRET), data);
    const res = await fetch(`https://${this.host}${path}`, {
      method,
      headers: {
        "EXN-API-KEY": this.env.EXN_API_KEY, "EXN-IDEMPOTENCY-KEY": idem, "EXN-TIMESTAMP": String(ts),
        "EXN-SIGN-VERSION": "1", "EXN-DATA": b64u(data), "EXN-SIGN": b64u(sig),
        // Without a User-Agent the API edge serves a bot challenge page.
        "User-Agent": "PartnerRewardsStudio/1.0", Accept: "application/json",
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? bodyBytes : undefined,
    });
    const text = await res.text();
    let payload;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = { message: `Non-JSON response (${text.slice(0, 80)})` }; }
    if (!res.ok) { const error = new ApiError(res.status, payload); error.path = path.split("?")[0]; throw error; }
    return payload;
  }

  async paged(path, params = "", limit = 200) {
    const rows = [];
    for (let offset = 0; ; offset += limit) {
      const q = params ? `${params}&` : "";
      const page = (await this.call("GET", `${path}?${q}limit=${limit}&offset=${offset}`)).data || [];
      rows.push(...page);
      if (page.length < limit) return rows;
    }
  }
}

// Demo client: used only by local `wrangler dev` when no API keys are set (see index.js → isDemo).
// Answers like a partner account with no clients and an empty wallet, and never moves money.
export class DemoExness {
  constructor() { this.demo = true; }
  async call(method, path) {
    if (method !== "GET") throw new ApiError(400, { message: "Demo mode — add Exness API keys to make payouts" });
    if (path.startsWith("/v1/partnership/partner/summary")) {
      return { uid: "demo", country: "—", clients_count: 0, summary_reward: { amount: 0 },
        accounts: [{ account: "DEMO-WALLET", account_type: "partner", archived: false }] };
    }
    if (/^\/v1\/accounts\/[^/]+\/balance/.test(path)) return { amount: 0, currency: "USD" };
    return { data: [] };
  }
  async paged() { return []; }
}
