CREATE TABLE participant_erasure (
  dataset TEXT NOT NULL,
  participant_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (dataset, participant_hash)
);
