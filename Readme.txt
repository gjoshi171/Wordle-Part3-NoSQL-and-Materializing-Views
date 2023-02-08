
Project: Wordle-Part3-NoSQL-and-Materializing-Views
======================

#Team Members: 
------------
Gaurav Joshi, 
Akhila Stanly


#Installation commands used

#For Redis
sudo apt update
sudo apt install --yes redis
redis-cli ping

#For Redis Client
sudo apt install --yes python3-hiredis


Execution Steps:

    Pre-requisites: 
    ---------------
        1. Project 3 Activities:
                Populating stats.db
                    1. Install faker using the terminal command sudo apt install --yes faker
                    2. Run stats.py using the command python3 stats.py (one-time activity)
                    3. This will generate stats.db using stats.sql file inside /sql directory
                    4. It will also populate the stats.db tables (users and games)
        2. Sharding of stats.db
                    1. stats.db has 2 tables users and games 
                    2. To shard users table(creating separate users.db): Run userSharding.py
                        Command used:
                            python3 userSharding.py
                        This will create a db called users.db with one table users
	
                    3. To shard games table and to create 3 separate games shards dbs : Run gameSharding.py
                        Command used:
                            python3 gameSharding.py
                        This will create 3 dbs called games1.db, games2.db and games3.db
                        Each of these dbs has its own table named games
        
        3. Shards of games db should be available inside /shard directory: games1.db, games2.db, games3.db
        4. Shard of users.db should be available inside /shard directory
        5. Script to shard views is available inside /sql directory - views.sql
    
    Scripts and Services:
    --------------------
    
    1. API for game states - gameState.py

        To run: uvicorn gameState:app --reload

        This microservice will connect only to the Redist datastore for States
        It will not connect to any shard dbs

        This api has 3 endpoints. 
            1. To insert new state of a new game
            2. To upadte the state of a game for each guess
            3. To fetch the state of a given userId and gameId

	2. Run viewSharding.py 

        To run: python3 viewSharding.py

        This will run views.sql (inside sql directory) and create views 'wins' and 'streaks' inside each shards db of games
    
    3. Run topWinsAndStreaks.py

        To run:     python3 topWinsAndStreaks.py

        This will take the top 10 entries for wins and streaks from each shards(3 shards of games). 
        Total 10*3 = 30 entries for each views and insert to sortedsets in Redis.
        Redis sortedset for top entries of wins >> winners
        Redis sortedset for top entries of streaks >> longestStreaks

    4. Scheduled topWinsAndStreaks.py in crontab

            crontab -l

            10 * * * * root python3 /var/workspace/project3/topWinsAndStreaks.py

        crontab is created to run topWinsAndStreaks.py every 10 mins (using insert mode in crontab -e and then saved using wq!)
        Thus statistics stored in Redis is updated from db every 10 mins
    

    5. Modified statistics.py from project-2

        To run:     uvicorn statistics:app --reload

        statistics.py is modified to use the shards of views to get topwinners and topstreaks
        new statistics.py has connections onlt to db shards
