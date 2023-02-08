from genericpath import exists
import json
from fastapi import FastAPI,status
from pydantic import BaseModel
from datetime import date
import redis

app = FastAPI()

# Service to start a new game
@app.get("/api/startnewgame/{userId}/{gameId}",status_code=status.HTTP_200_OK)
def start_new_game(userId, gameId):

    redisClient = redis.StrictRedis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

    #if user exists
    userGameUniqueId= f"{userId}:{gameId}"
    isUserPlaying=redisClient.exists(userGameUniqueId)
    if(isUserPlaying):
        print(redisClient.get(userGameUniqueId))
        return ("Error: Game has already been played")

    #if user does not exists
    currentStateAsDict = {
         "userID": userId,
         "gameID": gameId,
         "attempt_num": 0,
         "guesses": {
             "1": None,
             "2": None,
             "3": None,
             "4": None,
             "5": None,
             "6": None,
         }
     }

    redisClient.set(userGameUniqueId, json.dumps(currentStateAsDict))
    print("returned from new current state")
    print(currentStateAsDict)
    return currentStateAsDict

# Service to update the game state with a new guess
@app.get("/api/updategamestate/{userId}/{gameId}/{guess}",status_code=status.HTTP_200_OK)
def update_game_state(userId, gameId, guess):
    
    redisClient = redis.StrictRedis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    userGameUniqueId = f"{userId}:{gameId}"
    if (redisClient.exists(userGameUniqueId)):
        gameStateAsDict = json.loads(redisClient.get(userGameUniqueId))
    else:
        print("Errror: The game does not exist")
        return "Errror: The game does not exist"

    current_attempt_num = dict.get(gameStateAsDict, "attempt_num") + 1
    if (current_attempt_num+1) > 7:
        print(current_attempt_num+1)
        print("Error: 6 attempts have already been made")
        return "Error: 6 attempts have already been made"

    gameStateAsDict["attempt_num"] = current_attempt_num
    guesses_dict = dict.get(gameStateAsDict, "guesses")
    guesses_dict[current_attempt_num] = guess
    gameStateAsDict["guesses"] = guesses_dict
    
    redisClient.set(userGameUniqueId, json.dumps(gameStateAsDict))
    updatedGameState = json.loads(redisClient.get(userGameUniqueId))
    print(type(updatedGameState))
    print(current_attempt_num)
    return updatedGameState
    
# Service to get the state of an existing game
@app.get("/api/game/state/{userId}/{gameId}",status_code=status.HTTP_200_OK)
async def fetchState(userId, gameId):
    redisClient = redis.StrictRedis(host='localhost', port=6379, db=0)
    #if user exists
    userGameUniqueId= f"{userId}:{gameId}"
    isUserPlaying = redisClient.exists(userGameUniqueId)
    if(isUserPlaying):
        userGameState = json.loads(redisClient.get(userGameUniqueId))
        print(userGameState)
        return userGameState
    else:
        return None