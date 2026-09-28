import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from atlas.maintenance import backup, purge, retention_days, status
from atlas.messaging import database


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'work').mkdir()

    def test_retention_days_is_bounded(self):
        self.assertEqual(retention_days({}), 30)
        self.assertEqual(retention_days({'ATLAS_RETENTION_DAYS': '7'}), 7)
        for value in ('0', '366', 'many'):
            self.assertEqual(retention_days({'ATLAS_RETENTION_DAYS': value}), 30)

    def test_purge_removes_only_expired_records(self):
        path = self.root / 'work' / 'conversations.db'
        now = 2_000_000_000
        old, recent = now - 31 * 86400, now - 2 * 86400
        with database(path) as db:
            db.execute("INSERT INTO inbox(id,sender,body,timestamp) VALUES ('old','u','private',?)", (old,))
            db.execute("INSERT INTO inbox(id,sender,body,timestamp) VALUES ('new','u','current',?)", (recent,))
            db.execute("INSERT INTO progress(inbox_id,state) VALUES ('old','sent')")
            db.execute("INSERT INTO sessions(sender,step,data,updated_at) VALUES ('old','origin','{}',?)", (old,))
            db.execute("INSERT INTO sessions(sender,step,data,updated_at) VALUES ('new','origin','{}',?)", (recent,))
            db.execute('CREATE TABLE preferences '
                       '(sender TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at INTEGER NOT NULL)')
            db.execute("INSERT INTO preferences VALUES ('old','{}',?)", (old,))
            db.execute("INSERT INTO preferences VALUES ('new','{}',?)", (recent,))
        receipts = self.root / 'work' / 'webhooks.db'
        cutoff = datetime.fromtimestamp(now - 31 * 86400, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        current = datetime.fromtimestamp(recent, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        with closing(sqlite3.connect(receipts)) as db:
            db.execute('CREATE TABLE receipts (digest TEXT PRIMARY KEY, received_at TEXT)')
            db.execute("INSERT INTO receipts VALUES ('old',?)", (cutoff,))
            db.execute("INSERT INTO receipts VALUES ('new',?)", (current,))
            db.commit()
        result = purge(self.root, days=30, now=now)
        self.assertEqual(result, {'progress': 1, 'inbox': 1, 'sessions': 1,
                                  'preferences': 1, 'receipts': 1, 'retention_days': 30})
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute('SELECT id FROM inbox').fetchall(), [('new',)])
            self.assertEqual(db.execute('SELECT sender FROM sessions').fetchall(), [('new',)])

    def test_backup_creates_integrity_checked_snapshots(self):
        source = self.root / 'work' / 'conversations.db'
        with closing(sqlite3.connect(source)) as db:
            db.execute('CREATE TABLE sample (value TEXT)')
            db.execute("INSERT INTO sample VALUES ('kept')")
            db.commit()
        result = backup(self.root, self.root / 'snapshots',
                        datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(result['count'], 1)
        saved = Path(result['created'][0])
        self.assertEqual(saved.name, 'conversations-20260928T120000Z.db')
        with closing(sqlite3.connect(saved)) as db:
            self.assertEqual(db.execute('SELECT value FROM sample').fetchone()[0], 'kept')

    def test_status_contains_aggregates_without_private_content(self):
        path = self.root / 'work' / 'conversations.db'
        with database(path) as db:
            db.execute("INSERT INTO inbox(id,sender,body,timestamp) VALUES ('m','private-user','secret text',1)")
            db.execute("INSERT INTO sessions(sender,step,data) VALUES ('private-user','origin','{}')")
        result = status(self.root)
        rendered = str(result)
        self.assertEqual(result['storage'], 'ok')
        self.assertEqual(result['inbox'], {'pending': 1})
        self.assertEqual(result['sessions'], 1)
        self.assertNotIn('private-user', rendered)
        self.assertNotIn('secret text', rendered)


if __name__ == '__main__':
    unittest.main()
