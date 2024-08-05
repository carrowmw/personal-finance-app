# application/frontend/run.py
from application.frontend.app import app

if __name__ == "__main__":

    app.run(debug=True, port=5000)
