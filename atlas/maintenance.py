"""Local data retention and SQLite backup operations."""

import argparse
import json
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RETENTION_DAYS = 30


def retention_days(config):
    raw = str(config.get('ATLAS_RETENTION_DAYS', DEFAULT_RETENTION_DAYS)).strip()
    try:
        days = int(raw)
    except ValueError:
        return DEFAULT_RETENTION_DAYS
    return days if 1 <= days <= 365 else DEFAULT_RETENTION_DAYS


def _tables(db):
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def purge_conversations(path, cutoff):
    counts = {'progress': 0, 'inbox': 0, 'sessions': 0, 'preferences': 0}
    if not path.exists():
        return counts
    with closing(sqlite3.connect(path, timeout=10)) as db:
        tables = _tables(db)
        if 'progress' in tables and 'inbox' in tables:
            counts['progress'] = db.execute(
                'DELETE FROM progress WHERE inbox_id IN (SELECT id FROM inbox WHERE timestamp < ?)',
                (cutoff,),
            ).rowcount
        if 'inbox' in tables:
            counts['inbox'] = db.execute('DELETE FROM inbox WHERE timestamp < ?', (cutoff,)).rowcount
        for table in ('sessions', 'preferences'):
            if table in tables:
                columns = {row[1] for row in db.execute(f'PRAGMA table_info({table})')}
                if 'updated_at' in columns:
                    counts[table] = db.execute(
                        f'DELETE FROM {table} WHERE updated_at > 0 AND updated_at < ?', (cutoff,)
                    ).rowcount
        db.commit()
    return counts


def purge_receipts(path, days, now=None):
    if not path.exists():
        return 0
    now = int(time.time() if now is None else now)
    cutoff = datetime.fromtimestamp(now - days * 86400, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    with closing(sqlite3.connect(path, timeout=10)) as db:
        if 'receipts' not in _tables(db):
            return 0
        count = db.execute('DELETE FROM receipts WHERE received_at < ?', (cutoff,)).rowcount
        db.commit()
        return count


def purge(root=ROOT, days=DEFAULT_RETENTION_DAYS, now=None):
    now = int(time.time() if now is None else now)
    cutoff = now - days * 86400
    result = purge_conversations(root / 'work' / 'conversations.db', cutoff)
    result['receipts'] = purge_receipts(root / 'work' / 'webhooks.db', days, now)
    result['retention_days'] = days
    return result


def backup_database(source, destination):
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source, timeout=10)) as current:
        with closing(sqlite3.connect(destination)) as snapshot:
            current.backup(snapshot)
            if snapshot.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise sqlite3.DatabaseError('backup integrity check failed')
    return destination


def backup(root=ROOT, destination=None, instant=None):
    instant = instant or datetime.now(timezone.utc)
    stamp = instant.strftime('%Y%m%dT%H%M%SZ')
    destination = Path(destination or root / 'work' / 'backups')
    files = []
    for name in ('conversations.db', 'webhooks.db'):
        saved = backup_database(root / 'work' / name, destination / f'{name[:-3]}-{stamp}.db')
        if saved:
            files.append(str(saved.resolve()))
    return {'created': files, 'count': len(files)}


def status(root=ROOT):
    """Return aggregate operational facts without message text or traveler identifiers."""
    path = root / 'work' / 'conversations.db'
    result = {'storage': 'missing', 'database_bytes': 0, 'inbox': {}, 'sessions': 0,
              'preferences': 0, 'receipts': 0}
    if path.exists():
        result['database_bytes'] = path.stat().st_size
        try:
            with closing(sqlite3.connect(path, timeout=5)) as db:
                result['storage'] = 'ok' if db.execute('PRAGMA quick_check').fetchone()[0] == 'ok' else 'invalid'
                tables = _tables(db)
                if 'inbox' in tables:
                    result['inbox'] = dict(db.execute(
                        'SELECT state,COUNT(*) FROM inbox GROUP BY state').fetchall())
                if 'sessions' in tables:
                    result['sessions'] = db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
                if 'preferences' in tables:
                    result['preferences'] = db.execute('SELECT COUNT(*) FROM preferences').fetchone()[0]
        except sqlite3.Error:
            result['storage'] = 'unavailable'
    receipts = root / 'work' / 'webhooks.db'
    if receipts.exists():
        try:
            with closing(sqlite3.connect(receipts, timeout=5)) as db:
                if 'receipts' in _tables(db):
                    result['receipts'] = db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]
        except sqlite3.Error:
            if result['storage'] == 'ok':
                result['storage'] = 'partially_unavailable'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    purge_parser = commands.add_parser('purge', help='Delete local records older than the retention period.')
    purge_parser.add_argument('--days', type=int, default=DEFAULT_RETENTION_DAYS)
    backup_parser = commands.add_parser('backup', help='Create integrity-checked SQLite snapshots.')
    backup_parser.add_argument('destination', nargs='?', default=str(ROOT / 'work' / 'backups'))
    commands.add_parser('status', help='Print aggregate local health facts without personal data.')
    args = parser.parse_args()
    if args.command == 'purge':
        if not 1 <= args.days <= 365:
            parser.error('--days must be from 1 to 365')
        result = purge(days=args.days)
    elif args.command == 'backup':
        result = backup(destination=args.destination)
    else:
        result = status()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
