CREATE TABLE votes (
  vote_id TEXT PRIMARY KEY,
  dataset TEXT NOT NULL,
  fragment_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  method TEXT NOT NULL CHECK (method IN ('skilled', 'published', 'baseline')),
  participant_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE (dataset, fragment_id, participant_hash)
);
CREATE INDEX votes_dataset_method ON votes (dataset, method);
CREATE INDEX votes_dataset_participant ON votes (dataset, participant_hash);
CREATE TABLE rate_buckets (
  bucket_key TEXT PRIMARY KEY,
  count INTEGER NOT NULL CHECK (count > 0),
  expires_at INTEGER NOT NULL
);
CREATE INDEX rate_buckets_expiry ON rate_buckets (expires_at);
