"""
Centralized configuration for PlaylistPro.

All environment variables and settings are loaded here.
Import `config` to access settings throughout the application.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DatabaseConfig:
    """Database connection settings."""
    name: Optional[str] = None
    host: Optional[str] = None
    port: int = 3306
    user: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None

    def get_url(self) -> str:
        """Get the database URL, building from components if not set directly."""
        if self.url:
            return self.url
        if all([self.host, self.user, self.password, self.name]):
            return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return "sqlite:///playlistpro.db"

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.get_url().startswith("sqlite")


@dataclass
class OAuthConfig:
    """YouTube OAuth settings."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    project_id: Optional[str] = None
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    redirect_uris: List[str] = field(default_factory=lambda: ["http://localhost:5000"])

    def to_client_secret_dict(self) -> dict:
        """Convert to the format expected by Google OAuth library."""
        return {
            'web': {
                'client_id': self.client_id,
                'project_id': self.project_id,
                'auth_uri': self.auth_uri,
                'token_uri': self.token_uri,
                'auth_provider_x509_cert_url': self.auth_provider_url,
                'client_secret': self.client_secret,
                'redirect_uris': self.redirect_uris
            }
        }


@dataclass
class AppConfig:
    """Main application configuration."""
    # Environment
    environment: str = "development"
    debug_mode: bool = False
    verbose_debug: bool = False

    # Flask
    secret_key: Optional[bytes] = None
    host: str = "0.0.0.0"
    port: int = 5000

    # YouTube
    playlist_id: Optional[str] = None
    oauth_port: int = 8080
    project_id: int = 1

    # Sub-configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    oauth: OAuthConfig = field(default_factory=OAuthConfig)

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ('production', 'prod', 'docker')

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return not self.is_production


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    # Database config
    db_config = DatabaseConfig(
        name=os.environ.get('DATABASE'),
        host=os.environ.get('DATABASE_SERVER_IP'),
        port=int(os.environ.get('DATABASE_PORT', 3306)),
        user=os.environ.get('DATABASE_USER'),
        password=os.environ.get('DATABASE_PASSWORD'),
        url=os.environ.get('DATABASE_URL'),
    )

    # OAuth config
    redirect_uris_str = os.environ.get('REDIRECT_URIS', 'http://localhost:5000')
    oauth_config = OAuthConfig(
        client_id=os.environ.get('CLIENT_ID'),
        client_secret=os.environ.get('CLIENT_SECRET'),
        project_id=os.environ.get('PROJECT_ID'),
        auth_uri=os.environ.get('AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
        token_uri=os.environ.get('TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        auth_provider_url=os.environ.get('AUTH_PROVIDER', 'https://www.googleapis.com/oauth2/v1/certs'),
        redirect_uris=redirect_uris_str.split(',') if redirect_uris_str else [],
    )

    # Secret key - generate if not provided
    secret_key_env = os.environ.get('FLASK_SECRET_KEY')
    secret_key = secret_key_env.encode() if secret_key_env else None

    # Main config
    return AppConfig(
        environment=os.environ.get('ENVIRONMENT', os.environ.get('FLASK_ENV', 'development')),
        debug_mode=os.environ.get('DEBUG_MODE', '').lower() in ('true', '1', 'yes'),
        verbose_debug=os.environ.get('VERBOSE_DEBUG', '').lower() in ('true', '1', 'yes'),
        secret_key=secret_key,
        host=os.environ.get('HOST_IP', '0.0.0.0'),
        port=int(os.environ.get('HOST_PORT', 5000)),
        playlist_id=os.environ.get('YOUTUBE_PLAYLIST_ID'),
        oauth_port=int(os.environ.get('INTERNAL_FLOW_PORT', 8080)),
        project_id=int(os.environ.get('IDRIS_PROJECT_ID', 1)),
        database=db_config,
        oauth=oauth_config,
    )


# Global config instance - loaded once at import time
config = load_config()
