import sqlite3
import uuid

def shardGames():
    try:
        print("Games Sharding")
        sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
        sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

        #Creating connection of stats.db
        conn_stats = sqlite3.connect("./var/stats.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_stats = conn_stats.cursor()

        #Creating connection of users.db
        conn_users = sqlite3.connect("./shard/users.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_users = conn_users.cursor()

        #Creating connection of shards of games and creating games table in each shard
        i = 1
        while(i < 4):
            conn_shard = sqlite3.connect("./shard/games"+str(i)+".db", detect_types=sqlite3.PARSE_DECLTYPES)
            cursor_shard = conn_shard.cursor()
            cursor_shard.execute("CREATE TABLE IF NOT EXISTS games(user_id INTEGER NOT NULL, game_id INTEGER NOT NULL, finished DATE DEFAULT CURRENT_TIMESTAMP, guesses INTEGER,won BOOLEAN)")

            cursor_shard.close()
            conn_shard.close()
            i+=1
        
        #Get users from users.db
        users = cursor_users.execute("select * from users").fetchall()

        #Creating connection to all 3 shards of games
        
        conn_dict = {}
        cursor_dict = {}

        conn_games1 = sqlite3.connect("./shard/games1.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_games1 = conn_games1.cursor()
        conn_dict[1] = conn_games1
        cursor_dict[1] = cursor_games1

        conn_games2 = sqlite3.connect("./shard/games2.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_games2 = conn_games2.cursor()
        conn_dict[2] = conn_games2
        cursor_dict[2] = cursor_games2

        conn_games3 = sqlite3.connect("./shard/games3.db", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_games3 = conn_games3.cursor()
        conn_dict[3] = conn_games3
        cursor_dict[3] = cursor_games3

        for user in users:
            #Getting shard number from User's uuid modulo 3
            shard_num = (int(user[0]) % 3) + 1
            print(shard_num)
            currentConn = conn_dict[shard_num]
            currentCursor = cursor_dict[shard_num]
            print(user)
            #Getting user's games from stats.db games
            userGames = cursor_stats.execute("select * from games where user_id = ?",[user[1]]).fetchall()
            print(userGames)
            for userGame in userGames:
                print(userGame)
                currentCursor.execute("INSERT INTO games VALUES(:user_id, :game_id, :finished, :guesses, :won)", [userGame[0], userGame[1], userGame[2], userGame[3], userGame[4]])
                currentConn.commit()

        cursor_games1.close()
        cursor_games2.close()
        cursor_games3.close()
        conn_games1.close()
        conn_games2.close()
        conn_games3.close()

        cursor_users.close()
        conn_users.close()

        cursor_stats.close()
        conn_stats.close()

    except:
        print("Error!!")

shardGames()
