# livereload_server.py
"""
Advanced development server with live-reload for your Flask application.
This will automatically reload the page in your browser when you make changes
to Python files, templates, or static assets.
"""

import os
import threading
import time
from app import create_app
from livereload import Server


def run_livereload_server():
    app = create_app("development")
    app.debug = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # Add a test route to easily check if changes are reflected
    @app.route("/hot-reload-test")
    def hot_reload_test():
        return "Hot reload is working! Edit this text to test changes."

    # Create a live reload server
    server = Server(app.wsgi_app)

    # Watch Python files for changes
    server.watch("app/**/*.py")
    # Watch templates
    server.watch("app/templates/**/*.html")
    # Watch static files
    server.watch("app/static/**/*.css")
    server.watch("app/static/**/*.js")

    # Start the live reload server
    server.serve(port=5500, host="localhost", debug=True, open_url_delay=0.5)


if __name__ == "__main__":
    print("Starting LiveReload development server...")
    print("Visit http://localhost:5500/ to view your application")
    print("Make changes to your code and the browser will automatically refresh!")

    # Add a slight delay to ensure proper startup
    time.sleep(1)

    # Run the server
    run_livereload_server()
