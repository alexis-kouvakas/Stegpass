"""Module containing functions for interacting with the database."""
import contextlib
from collections.abc import Iterator
from pathlib import Path
from sqlite3 import DatabaseError
from typing import TYPE_CHECKING

from stegpass.database_exceptions import PasswordValidationError

from pysqlcipher3 import dbapi2 as sqlite

if TYPE_CHECKING:
    from sqlite3 import Cursor


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
            "CREATE TABLE Passwords "
            "(PasswordId INTEGER PRIMARY KEY, Password TEXT NOT NULL);"
        )
        cursor.close()
        conn.commit()
    return vault_path.exists()


@contextlib.contextmanager
def access_vault(
    vault_path: Path,
    master_password: str,
    should_commit: bool = False,
) -> Iterator["Cursor | Exception"]:
    """Attempt to connect to the database at `vault_path` with `master_password`.

    :param vault_path: Path to the new vault
    :param master_password: The password to lock the vault with
    :yield: Connection object if successful, otherwise a subclass of Exception
    """
    if not vault_path.exists():
        return FileNotFoundError(f"\"{vault_path}\" does not exist")
    else:
        conn =  sqlite.connect(vault_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key='{master_password}';")
        try:
            # Checking if the password was correct
            cursor.execute("PRAGMA schema_version;")
        except DatabaseError as e:
            return PasswordValidationError(e)
        # Must yield conn within try-finally so it is properly closed
        try:
            yield cursor 
        finally:
            if should_commit:
                conn.commit()
            cursor.close()
            conn.close()
