"""Explicitly saved travel defaults, separate from conversation history."""

import json
import sqlite3
from contextlib import closing


FIELDS = ('origin', 'adults', 'priority')


class Preferences:
    def __init__(self, path=None):
        self.path = path
        self.memory = {}
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path, timeout=10)) as db:
                db.execute('CREATE TABLE IF NOT EXISTS preferences (sender TEXT PRIMARY KEY, data TEXT NOT NULL)')
                db.commit()

    def load(self, user):
        if self.path is None:
            return dict(self.memory.get(user, {}))
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            row = db.execute('SELECT data FROM preferences WHERE sender=?', (user,)).fetchone()
        return json.loads(row[0]) if row else {}

    def save(self, user, values):
        data = {key: values[key] for key in FIELDS}
        if self.path is None:
            self.memory[user] = data
        else:
            with closing(sqlite3.connect(self.path, timeout=10)) as db:
                db.execute('INSERT OR REPLACE INTO preferences VALUES (?,?)', (user, json.dumps(data)))
                db.commit()

    def delete(self, user):
        if self.path is None:
            self.memory.pop(user, None)
        else:
            with closing(sqlite3.connect(self.path, timeout=10)) as db:
                db.execute('DELETE FROM preferences WHERE sender=?', (user,))
                db.commit()


def describe(values):
    priorities = {'1': 'menor preço', '2': 'menor duração', '3': 'sem paradas', '4': 'maior preço'}
    return (f"• Origem: {values['origin']}\n"
            f"• Passageiros: {values['adults']} adulto(s)\n"
            f"• Preferência: {priorities[values['priority']]}")
