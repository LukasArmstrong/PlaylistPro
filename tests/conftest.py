"""
Pytest configuration and fixtures for PlaylistPro tests.
"""

import os
import pytest
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables before importing app modules
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
os.environ['ENVIRONMENT'] = 'development'


@pytest.fixture(scope='session')
def app():
    """Create Flask application for testing."""
    from flask import Flask
    from pywertube import db, init_db

    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'test-secret-key'

    init_db(app)

    yield app


@pytest.fixture(scope='function')
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a fresh database session for each test."""
    from pywertube import db

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def sample_video_tuple():
    """Sample video data in tuple format."""
    return (
        0,                      # position
        'PLtest123',            # playlistID
        'dQw4w9WgXcQ',         # videoID
        212.0,                  # duration (seconds)
        'Rick Astley',          # creator
        1256918400,             # publishedTimeUTC (epoch)
        'Never Gonna Give You Up'  # title
    )


@pytest.fixture
def sample_watch_later_list(sample_video_tuple):
    """Sample watch later list with multiple videos."""
    return [
        sample_video_tuple,
        (1, 'PLtest123', 'video2', 300.0, 'Creator A', 1256918500, 'Video Two'),
        (2, 'PLtest123', 'video3', 180.0, 'Creator B', 1256918600, 'Video Three'),
        (3, 'PLtest123', 'video4', 600.0, 'Creator A', 1256918700, 'Video Four'),
        (4, 'PLtest123', 'video5', 120.0, 'Creator C', 1256918800, 'Video Five'),
    ]
