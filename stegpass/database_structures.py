"""Module containing the database schema."""
from dataclasses import dataclass


@dataclass
class Login:
    """Row in the Logins table."""
    login_id: int
    username: str
    password: str
    uri: str
