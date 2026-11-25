-- Partner Rewards Studio — D1 schema
CREATE TABLE IF NOT EXISTS promos (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  condition TEXT NOT NULL,          -- ftd | kyc
  amount REAL NOT NULL,
  start TEXT NOT NULL,              -- YYYY-MM-DD (UTC)
  "end" TEXT NOT NULL,
  budget REAL,
  wallet TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',  -- active | ended
  test INTEGER NOT NULL DEFAULT 0,
  baseline TEXT NOT NULL DEFAULT '[]',    -- JSON array of client_uid excluded at launch
  created_at TEXT NOT NULL,
  ended_at TEXT,
  last_scan TEXT,
  auto_pay INTEGER NOT NULL DEFAULT 0,    -- 1 = send bonuses automatically (cron), within budget
  auto_note TEXT,                         -- last auto-pay problem (e.g. low wallet balance)
  audience TEXT NOT NULL DEFAULT 'new',   -- new = registered in [start, end]; existing = registered before start
  hidden INTEGER NOT NULL DEFAULT 0,      -- 1 = removed from the promotions list (data and payout history kept)
  currency TEXT NOT NULL DEFAULT 'USD'    -- USD = Reward Wallet transfer; EXD = partnership EXD transfer
);

CREATE TABLE IF NOT EXISTS qualified (
  promo_id TEXT NOT NULL,
  uid TEXT NOT NULL,
  observed TEXT NOT NULL,           -- date first seen qualified
  at TEXT NOT NULL,
  PRIMARY KEY (promo_id, uid)
);

CREATE TABLE IF NOT EXISTS payouts (
  promo_id TEXT NOT NULL,
  uid TEXT NOT NULL,
  account TEXT NOT NULL,
  amount REAL NOT NULL,
  idem TEXT NOT NULL,               -- idempotency key of the current attempt
  status TEXT NOT NULL,             -- queued | sending | retry | processing | done | sent (EXD accepted) | failed | rejected
  transfer_id TEXT,
  error TEXT,
  attempts TEXT NOT NULL DEFAULT '[]',
  new_key_tries INTEGER NOT NULL DEFAULT 0,
  next_attempt_at INTEGER NOT NULL DEFAULT 0,  -- epoch ms
  lock_until INTEGER NOT NULL DEFAULT 0,       -- epoch ms, claim for 'sending'
  created TEXT NOT NULL,
  sent_at TEXT,
  finished_at TEXT,
  PRIMARY KEY (promo_id, uid)
);

CREATE TABLE IF NOT EXISTS accounts (
  uid TEXT PRIMARY KEY,
  account TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
