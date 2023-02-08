#!/usr/bin/env python3
# stand-alone program to schedule in crontab. 
# This will update the wins and streaks views based on the updates in games tables 

import sqlite3
import redis

def fetchDataFromShard(viewDictionary, shardDb, script):
    connection = sqlite3.connect(shardDb)
    cursor = connection.cursor()

    dbResult = cursor.execute(script).fetchall()
    cursor.close()
    connection.close()

    for d in dbResult:
        viewDictionary[d[0]]=d[1]
    
    return viewDictionary

def findTopEntries():
    redisClient = redis.StrictRedis(host='localhost', port=6379, db=0)
    redisClient.set("message", "Redis Connected!!!")
    msg = redisClient.get("message")
    print(msg)

    redisClient.flushall()
    redisClient.flushdb()

    games1db = "./shard/games1.db"
    games2db = "./shard/games2.db"
    games3db = "./shard/games3.db"

    winsDict = {}
    winsScript = "SELECT user_id,count from wins limit 10"

    winsDict = fetchDataFromShard(winsDict, games1db, winsScript)
    winsDict = fetchDataFromShard(winsDict, games2db, winsScript)
    winsDict = fetchDataFromShard(winsDict, games3db, winsScript)
    
    winners = "winners"

    redisClient.zadd(winners,winsDict)
    print("Top Winners")
    print(redisClient.zrange(winners, 0, -1, desc=True, withscores=True))
    print("Count of top winners = "+str(redisClient.zcard(winners)))
    print("----------")

    streaksDict = {}
    streaksScript = "SELECT user_id,streak from streaks order by streak desc limit 10"

    streaksDict = fetchDataFromShard(streaksDict, games1db, streaksScript)
    streaksDict = fetchDataFromShard(streaksDict, games2db, streaksScript)
    streaksDict = fetchDataFromShard(streaksDict, games3db, streaksScript)

    longestStreaks = "longestStreaks"

    redisClient.zadd(longestStreaks,streaksDict)
    print("Top Streaks")
    print(redisClient.zrange(longestStreaks, 0, -1, desc=True, withscores=True))
    print("Count of top streaks = "+str(redisClient.zcard(longestStreaks)))


findTopEntries()