#!/bin/bash

# Activate virtual environment
source /home/administrator/personal-finances/.venv/bin/activate

# Remove existing cursor file
rm -f /home/administrator/personal-finances/application/backend/cursor.json
rm -f /home/administrator/personal-finances/application/data/balance.pkl
rm -f /home/administrator/personal-finances/application/data/transactions.pkl

# Kill any process currently using port 5010 (frontend)
FRONTEND_PORT=5010
FRONTEND_PIDS=$(lsof -t -i:$FRONTEND_PORT)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "Killing processes using port $FRONTEND_PORT"
    kill -9 $FRONTEND_PIDS
fi

# Kill any process currently using port 5030 (backend)
BACKEND_PORT=5030
BACKEND_PIDS=$(lsof -t -i:$BACKEND_PORT)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo "Killing processes using port $BACKEND_PORT"
    kill -9 $BACKEND_PIDS
fi

sleep 1

# Change to project directory
cd /home/administrator/personal-finances

# Export environment variables for Flask
export FLASK_APP=application/backend/run.py
export FLASK_DEBUG=0  # Changed to 0 for production

# Start the backend server in the background
flask run --host=0.0.0.0 --port=5030 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for the backend server to start
sleep 2

# Tail the backend log file to see logs in real-time
tail -f backend.log &

# Export environment variables for Flask frontend
export FLASK_APP=application/frontend/run.py
export FLASK_DEBUG=0  # Changed to 0 for production

# Start the frontend server in the background
flask run --host=0.0.0.0 --port=5010 > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for the frontend server to start
sleep 2

# Tail the frontend log file to see logs in real-time
tail -f frontend.log &

# Wait for the frontend and backend servers to finish
wait $FRONTEND_PID
wait $BACKEND_PID