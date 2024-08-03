"""Module containing functions for interacting with the database."""
import contextlib
from collections.abc import Iterator
from pathlib import Path
from sqlite3 import DatabaseError
from typing import TYPE_CHECKING

import pysqlcipher3.dbapi2 as sqlite

from stegpass.database_exceptions import PasswordValidationError
from stegpass.database_queries import LoginQuery


if TYPE_CHECKING:
    from sqlite3 import Connection


def create_vault(vault_path: Path, master_password: str) -> bool:
    """Create a database with provided path and password.

    :param vault_path: Path to the new vault
    :param master_password: The password to lock the vault with
    :return: Whether a new vault was successfully created
    """
    if vault_path.exists():
        return False
    with sqlite.connect(vault_path) as conn:
        cursor = conn.cursor()
        # TODO Sanitize master_password
        cursor.execute(f"PRAGMA key='{master_password}';")
        cursor.execute(
            "CREATE TABLE Logins("
            "LoginId INTEGER PRIMARY KEY, "
            "Username TEXT NOT NULL, "
            "Password TEXT NOT NULL, "
            "URI TEXT NULL"
            ");"
        )
        cursor.close()
        conn.commit()
    return vault_path.exists()


@contextlib.contextmanager
def access_vault(
    vault_path: Path,
    master_password: str,
) -> Iterator["Connection | Exception"]:
    """Attempt to connect to a database with a master password.

    :param vault_path: Path to the new vault
    :param master_password: The password to lock the vault with
    :yield: Connection object if successful, otherwise a subclass of Exception
    """
    if not vault_path.exists():
        yield FileNotFoundError(f"\"{vault_path}\" does not exist")
    else:
        conn = sqlite.connect(vault_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key='{master_password}';")
        try:
            # Checking if the password was correct
            cursor.execute("PRAGMA schema_version;")
        except DatabaseError:
            yield PasswordValidationError()
        cursor.close()  # Closing the cursor keeps the database unlocked
        # Must yield conn within try-finally so it is properly closed
        try:
            yield conn
        finally:
            print("lol")
            conn.close()


def save_login(
    vault_path: Path,
    master_password: str,
    login: LoginQuery,
) -> bool:
    if not vault_path.exists():
        return False
    with access_vault(vault_path, master_password) as conn:
        if isinstance(conn, Exception):
            raise conn
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Logins (LoginName, Password) VALUES (?, ?)",
            (login.login_name, login.password),
        )
        cursor.close()
        conn.commit()
        return conn.total_changes > 0
