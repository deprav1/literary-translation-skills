import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VoteMigrationTests(unittest.TestCase):
    def test_preserves_old_vote_and_admits_new_method(self):
        db = sqlite3.connect(':memory:')
        db.executescript((ROOT / 'backend/migrations/0001_votes.sql').read_text(encoding='utf8'))
        old = ('v1', 'old', 'fragment', 'candidate', 'published', 'hash', 123)
        db.execute('INSERT INTO votes VALUES (?, ?, ?, ?, ?, ?, ?)', old)
        db.commit()
        db.executescript((ROOT / 'backend/migrations/0003_reviewed_method.sql').read_text(encoding='utf8'))
        self.assertEqual(db.execute('SELECT * FROM votes').fetchall(), [old])
        db.execute('INSERT INTO votes VALUES (?, ?, ?, ?, ?, ?, ?)',
                   ('v2', 'new', 'fragment', 'candidate', 'reviewed', 'hash', 124))
        self.assertEqual(db.execute('SELECT COUNT(*) FROM votes').fetchone()[0], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute('INSERT INTO votes VALUES (?, ?, ?, ?, ?, ?, ?)',
                       ('v3', 'new', 'fragment', 'candidate', 'reviewed', 'hash', 125))


if __name__ == '__main__':
    unittest.main()
