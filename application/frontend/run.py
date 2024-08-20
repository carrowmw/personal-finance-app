# application/frontend/run.py

from application.frontend.src import create_app

app = create_app()
print(
    "Debug mode for frontend is", app.debug
)  # This will output the debug status when the app starts

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
