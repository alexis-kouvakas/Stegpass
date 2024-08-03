"""Module containing the database schema."""
from dataclasses import dataclass


@dataclass
class Login:
    """Row in the Logins table."""
    login_id: int
    login_name: str
    password: str
