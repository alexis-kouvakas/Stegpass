"""Module containing database table aggregates (without primary key)."""
from dataclasses import dataclass


@dataclass
class LoginQuery:
    """Columns for the Logins table"""
    login_name: str
    password: str
