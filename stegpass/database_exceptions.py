"""Module containing exceptions thrown interacting with the database"""
from sqlite3 import Error


class PasswordValidationError(Error):
    pass
