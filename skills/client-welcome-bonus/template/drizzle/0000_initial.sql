CREATE TABLE IF NOT EXISTS promos (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  condition TEXT NOT NULL,
  amount REAL NOT NULL,
  start TEXT NOT NULL,
  "end" TEXT NOT NULL,
  budget REAL,
  wallet TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  test INTEGER NOT NULL DEFAULT 0,
  baseline TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  ended_at TEXT,
  last_scan TEXT,
  auto_pay INTEGER NOT NULL DEFAULT 0,
  auto_note TEXT,
  audience TEXT NOT NULL DEFAULT 'new',
  hidden INTEGER NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'USD'
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS qualified (
  promo_id TEXT NOT NULL,
  uid TEXT NOT NULL,
  observed TEXT NOT NULL,
  at TEXT NOT NULL,
  PRIMARY KEY (promo_id, uid)
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS payouts (
  promo_id TEXT NOT NULL,
  uid TEXT NOT NULL,
  account TEXT NOT NULL,
  amount REAL NOT NULL,
  idem TEXT NOT NULL,
  status TEXT NOT NULL,
  transfer_id TEXT,
  error TEXT,
  attempts TEXT NOT NULL DEFAULT '[]',
  new_key_tries INTEGER NOT NULL DEFAULT 0,
  next_attempt_at INTEGER NOT NULL DEFAULT 0,
  lock_until INTEGER NOT NULL DEFAULT 0,
  created TEXT NOT NULL,
  sent_at TEXT,
  finished_at TEXT,
  PRIMARY KEY (promo_id, uid)
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS accounts (
  uid TEXT PRIMARY KEY,
  account TEXT NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);
