import sqlite3
import uuid

def shardUsers():
    try:
        sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
        sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

        #Creating connection of stats.db
        conn_stats = sqlite3.connect("./var/stats.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_stats = conn_stats.cursor()

        #Creating connection of new users.db
        conn_users = sqlite3.connect("./shard/users.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_users = conn_users.cursor()

        #Execute create users table in users.db
        cursor_users.execute("CREATE TABLE IF NOT EXISTS users(uuid GUID, user_id INTEGER NOT NULL, username VARCHAR UNIQUE)")

        #Execute fetch All users data from stats.db
        users = cursor_stats.execute("select * from users").fetchall()

        for usr in users:
            try:
                user_id = int(usr[0])
                
                username = usr[1]
                user_uuid = uuid.uuid4() #generate uuid
                
                #Execute insert into users table in users.db each  record from stats.db
                cursor_users.execute("INSERT INTO users VALUES(:uuid,:user_id,:username)",[user_uuid, user_id, username])
                conn_users.commit()
            except sqlite3.IntegrityError:
                continue
        
        conn_users.close()
        conn_stats.close()
    except:
        print("ERROR!")


shardUsers()