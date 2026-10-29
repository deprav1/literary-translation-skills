-- Retain all existing votes while admitting the fourth comparison condition.
CREATE TABLE votes_new (
  vote_id TEXT PRIMARY KEY,
  dataset TEXT NOT NULL,
  fragment_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  method TEXT NOT NULL CHECK (method IN ('skilled', 'published', 'baseline', 'reviewed')),
  participant_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  UNIQUE (dataset, fragment_id, participant_hash)
);
INSERT INTO votes_new (vote_id, dataset, fragment_id, candidate_id, method, participant_hash, created_at)
  SELECT vote_id, dataset, fragment_id, candidate_id, method, participant_hash, created_at FROM votes;
DROP TABLE votes;
ALTER TABLE votes_new RENAME TO votes;
CREATE INDEX votes_dataset_method ON votes (dataset, method);
CREATE INDEX votes_dataset_participant ON votes (dataset, participant_hash);
