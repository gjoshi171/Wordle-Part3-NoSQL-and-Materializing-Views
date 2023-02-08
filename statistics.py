from http.client import HTTPException
import sqlite3
import uuid
from fastapi import FastAPI,status
from pydantic import BaseModel
from datetime import date, timedelta
import redis
import contextlib

app = FastAPI()

#service to retrieve top 10 users by number of wins
@app.get("/api/stats/topwinners",status_code=status.HTTP_200_OK)
async def topWinners():

    redisClient = redis.StrictRedis(host='localhost', port=6379, db=0)
    print(redisClient.zcard("winners"))
    return redisClient.zrange("winners", 0, 9, desc=True, withscores=False)

#service to retrieve top 10 users by longest streak
@app.get("/api/stats/topstreaks",status_code=status.HTTP_200_OK)
async def topStreaks():

    redisClient = redis.StrictRedis(host='localhost', port=6379, db=0)
    print(redisClient.zcard("longestStreaks"))
    return redisClient.zrange("longestStreaks", 0, 9, desc=True, withscores=False)


#Models for Statistics API
class Guesses(BaseModel):
    g1: int
    g2: int
    g3: int
    g4: int
    g5: int
    g6: int
    fail: int

class Statistics(BaseModel):
    currentStreak: int
    maxStreak: int
    guesses: Guesses
    winPercentage: float
    gamesPlayed: int
    gamesWon: int
    averageGuesses: int

class Game(BaseModel):
    userId: int
    gameId: int
    finished: str
    guesses: int
    won: bool

#service to post the win or loss of a game, along with timestamp and number of guesses
@app.post("/api/game/result")
async def postGameResult(game: Game):
    try:
        print("try")
        sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
        sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)

        #connection to users shard
        users_connection = sqlite3.connect("./shard/users.db", detect_types=sqlite3.PARSE_DECLTYPES)
        users_cursor = users_connection.cursor()

        gameShardNum = 0
        print(gameShardNum)
        users = users_cursor.execute("select * from users").fetchall()
        if users is not None and len(users):
            for u in users:
                if(str(u[1])==str(game.userId)):
                    gameShardNum = (int(u[0]) % 3) + 1
                    break
        print(gameShardNum)
        gamesdb_dict ={}

        gamesdb_dict = {
            1: "./shard/games1.db",
            2: "./shard/games2.db",
            3: "./shard/games3.db",
        }

        gamesdb = gamesdb_dict[gameShardNum]
        print(gamesdb)
        
        with contextlib.closing(sqlite3.connect(gamesdb)) as db:
            x = db.execute("INSERT INTO games(user_id, game_id, finished, guesses, won) VALUES(?, ?, ?, ?, ?)",
                    [game.userId, game.gameId, game.finished, game.guesses, game.won])
            print(x)
            db.commit()
            db.close()
        
    except sqlite3.IntegrityError:
        print("Error!!")

#service to retrieve statistics for a user
@app.get("/api/stats/statistics/{userid}", status_code=status.HTTP_200_OK)
async def statistics(userid):
    try:
        sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
        sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)
        gamesPlayed = 0
        gamesWon = 0
        fail =0
        avgGuesses = 0
        currentStreak = 0
        maxStreak = 0
        guesses = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0}

        #connection to users shard
        users_connection = sqlite3.connect("./shard/users.db", detect_types=sqlite3.PARSE_DECLTYPES)
        users_cursor = users_connection.cursor()

        gameShardNum = 0

        users = users_cursor.execute("select * from users").fetchall()
        if users is not None and len(users):
            for u in users:
                if(str(u[1])==str(userid)):
                    gameShardNum = (int(u[0]) % 3) + 1
                    break
        #print(gameShardNum)
        gamesdb_dict ={}

        gamesdb_dict = {
            1: "./shard/games1.db",
            2: "./shard/games2.db",
            3: "./shard/games3.db",
        }

        gamesdb = gamesdb_dict[gameShardNum]
        #print(gamesdb)
        
        #connection to the corresponding games shard based on the shard num
        conn_games = sqlite3.connect(gamesdb, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor_games = conn_games.cursor()

        gamesResult = cursor_games.execute("SELECT guesses,won from games where user_id=?",[userid]).fetchall()
        #print(gamesResult)
        
        if gamesResult is not None:
            gamesPlayed = len(gamesResult)
            print(gamesPlayed)
            for g in gamesResult:
                guesses[g[0]]+=1
                if g[1] == 0:
                    fail+=1
            i = 1
            sumOfGuesses = 0
            while i <= 6:
                sumOfGuesses += i*guesses[i]
                i +=1

            winsResult = cursor_games.execute("SELECT * from wins where user_id = ?",[userid]).fetchall()
            if winsResult is not None and len(winsResult)>0:
                gamesWon = winsResult[0][1]

            if gamesPlayed == 0:
                winPercentage = 0
            else:
                winPercentage = (gamesWon/gamesPlayed)*100
                avgGuesses = round(sumOfGuesses/gamesPlayed)

            streakResult = cursor_games.execute("SELECT streak from streaks where user_id = ? order by ending desc",[userid]).fetchall()

            if (streakResult is not None and len(streakResult)>0 and streakResult[0] is not None and len(streakResult[0])>0):
                currentStreak = streakResult[0][0]
            else:
                currentStreak = 0

            maxStreakResult = cursor_games.execute("SELECT MAX(streak) from streaks where user_id = ? order by ending desc",[userid]).fetchall()
            if (maxStreakResult is not None and len(maxStreakResult)>0):
                if len(maxStreakResult[0])!=0 and maxStreakResult[0][0] is not None:
                    maxStreak = maxStreakResult[0][0]
                else:
                    maxStreak = 0

            g = Guesses(g1=guesses[1], g2=guesses[2], g3=guesses[3], g4=guesses[4], g5=guesses[5], g6=guesses[6], fail=fail ) 
            stat = Statistics(currentStreak=currentStreak, maxStreak=maxStreak, guesses=g, winPercentage=round(winPercentage, 2), gamesPlayed=gamesPlayed, gamesWon=gamesWon, averageGuesses=avgGuesses)
        
        cursor_games.close()
        conn_games.close()
        users_cursor.close()
        users_connection.close()

    except:
        print("Error!!")

    return stat