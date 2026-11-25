// Cloudflare Access JWT verification (defence in depth behind the Access policy).
// Fails closed: if ACCESS_TEAM_DOMAIN / ACCESS_AUD are not configured, nobody gets in.

let certs = null, certsAt = 0;

const b64uToBytes = (s) => {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(s + "===".slice((s.length + 3) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
};
const b64uJson = (s) => JSON.parse(new TextDecoder().decode(b64uToBytes(s)));

async function getCerts(team) {
  if (certs && Date.now() - certsAt < 3600_000) return certs;
  const r = await fetch(`https://${team}/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error("Cannot load Access certs");
  certs = (await r.json()).keys;
  certsAt = Date.now();
  return certs;
}

function tokenFrom(req) {
  const h = req.headers.get("cf-access-jwt-assertion");
  if (h) return h;
  const m = (req.headers.get("cookie") || "").match(/(?:^|;\s*)CF_Authorization=([^;]+)/);
  return m ? m[1] : null;
}

export async function authenticate(req, env) {
  const url = new URL(req.url);
  // Local development only: never honoured on a real hostname.
  if (env.DEV_BYPASS_EMAIL && ["localhost", "127.0.0.1"].includes(url.hostname)) return env.DEV_BYPASS_EMAIL;

  const team = (env.ACCESS_TEAM_DOMAIN || "").replace(/^https?:\/\//, "").replace(/\/$/, "");
  const aud = env.ACCESS_AUD;
  if (!team || !aud) throw new AuthError("Cloudflare Access is not configured for this app yet");
  const token = tokenFrom(req);
  if (!token) throw new AuthError("Sign in required");
  const parts = token.split(".");
  if (parts.length !== 3) throw new AuthError("Bad token");
  const header = b64uJson(parts[0]), payload = b64uJson(parts[1]);
  const jwk = (await getCerts(team)).find((k) => k.kid === header.kid);
  if (!jwk) throw new AuthError("Unknown signing key");
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64uToBytes(parts[2]),
    new TextEncoder().encode(`${parts[0]}.${parts[1]}`));
  if (!ok) throw new AuthError("Bad signature");
  const now = Math.floor(Date.now() / 1000);
  const auds = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!auds.includes(aud)) throw new AuthError("Wrong audience");
  if (payload.iss !== `https://${team}`) throw new AuthError("Wrong issuer");
  if (!payload.exp || payload.exp < now) throw new AuthError("Session expired");
  const email = (payload.email || "").toLowerCase();
  const allowed = (env.ALLOWED_EMAILS || "").toLowerCase().split(",").map((s) => s.trim()).filter(Boolean);
  if (!allowed.length || !allowed.includes(email)) throw new AuthError("This account is not allowed");
  return email;
}

export class AuthError extends Error {}
