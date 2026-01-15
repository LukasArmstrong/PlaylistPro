"""
Database configuration for PlaylistPro.

This module provides the SQLAlchemy database instance that is shared
across the application. It supports multiple database backends:

- SQLite (default): Zero configuration, perfect for development
- MariaDB/MySQL: Production-ready with PyMySQL driver
- PostgreSQL: Alternative production option

Configuration via DATABASE_URL environment variable:
    SQLite:   sqlite:///playlistpro.db
    MariaDB:  mysql+pymysql://user:pass@localhost:3306/dbname
    Postgres: postgresql://user:pass@localhost:5432/dbname
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    Initialize the database with a Flask application.

    Args:
        app: Flask application instance

    This function should be called during application setup to bind
    the SQLAlchemy instance to the Flask app.
    """
    db.init_app(app)

    with app.app_context():
        db.create_all()
