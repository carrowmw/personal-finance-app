#!/bin/bash

# Remove existing cursor file
rm application/backend/cursor.json
rm application/data/balance.pkl
rm application/data/transactions.pkl

# Kill any process currently using port 5030 (backend)
PORT=5030
PID=$(lsof -t -i:$PORT)
if [ ! -z "$PID" ]; then
    echo "Killing process $PID using port $PORT"
    kill -9 $PID
fi

# Start the backend server with unbuffered output
PYTHONUNBUFFERED=1
export FLASK_APP=application/backend/src/server.py
flask run --host=0.0.0.0 --port=5030 > backend.log 2>&1 &

# Wait for the backend server to start
sleep 2

# Tail the backend log file to see logs in real-time
tail -f backend.log &

# Start the frontend server
poetry run python application/frontend/run.py