import contextlib
import sqlite3

SCHEMA = './sql/views.sql'

DATABASE1 = './shard/games1.db'

with contextlib.closing(sqlite3.connect(DATABASE1)) as db1:
    with open(SCHEMA) as f:
        db1.executescript(f.read())
    db1.commit()
    db1.close()

DATABASE2 = './shard/games2.db'

with contextlib.closing(sqlite3.connect(DATABASE2)) as db2:
    with open(SCHEMA) as f:
        db2.executescript(f.read())
    db2.commit()
    db2.close()

DATABASE3 = './shard/games3.db'

with contextlib.closing(sqlite3.connect(DATABASE3)) as db3:
    with open(SCHEMA) as f:
        db3.executescript(f.read())
    db3.commit()
    db3.close()