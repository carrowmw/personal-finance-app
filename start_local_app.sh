# /start.sh

# Remove existing cursor file
rm -f application/backend/cursor.json
rm -f application/data/balance.pkl
rm -f application/data/transactions.pkl

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

# Export environment variables for Flask
export FLASK_APP=application/backend/run.py
export FLASK_DEBUG=1

# Start the backend server in the background
flask run --host=localhost --port=5030 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for the backend server to start
sleep 2

# Tail the backend log file to see logs in real-time
tail -f backend.log &

# Export environment variables for Flask frontend
export FLASK_APP=application/frontend/run.py
export FLASK_DEBUG=1

# Start the frontend server in the background
flask run --host=localhost --port=5010 > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for the frontend server to start
sleep 2

# Tail the frontend log file to see logs in real-time
tail -f frontend.log &

# Wait for the frontend and backend servers to finish
wait $FRONTEND_PID
wait $BACKEND_PID