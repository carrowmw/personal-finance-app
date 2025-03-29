# tests/test_app.py

# tests/test_app.py
import pytest
from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


def test_home_page(client):
    """Test home page loads."""
    response = client.get("/")
    assert response.status_code == 200


def test_register_page(client):
    """Test registration page loads."""
    response = client.get("/register")
    assert response.status_code == 200
