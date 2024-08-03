"""Module containing functions for interacting with the database."""
import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import pysqlcipher3.dbapi2 as sqlite

from stegpass.database_exceptions import PasswordValidationError
from stegpass.database_queries import LoginQuery
from stegpass.database_structures import Login


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
    with sqlite.connect(str(vault_path)) as conn:
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
        conn = sqlite.connect(str(vault_path))
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key='{master_password}';")
        try:
            # Checking if the password was correct
            cursor.execute("PRAGMA schema_version;")
        except sqlite.DatabaseError:
            yield PasswordValidationError()
        else:
            cursor.close()  # Closing the cursor keeps the database unlocked
            yield conn
            conn.close()


def save_login(
    vault_path: Path,
    master_password: str,
    login: LoginQuery,
) -> bool | None:
    if not vault_path.exists():
        return None
    with access_vault(vault_path, master_password) as conn:
        if isinstance(conn, Exception):
            return None
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Logins (Username, Password, URI) "
            "VALUES (?, ?, ?)",
            (login.username, login.password, login.uri),
        )
        cursor.close()
        conn.commit()
        success = conn.total_changes > 0
    return success


def get_logins_by_query(
    vault_path: Path,
    master_password: str,
    *,
    uri: str | None = None,
    username: str | None = None
) -> Sequence[Login] | None:
    """Return a sequence of Logins where uri and/or username is a substring.

    If the password is incorrect, return None.
    If both uri and username are None or empty strings, return None.
    If no rows are found, return an empty list.

    :param vault_path: Path to the vault file
    :param master_password: Password to unlock the vault
    :param uri: The URI to match in the database
    :param username: The username to match in the database
    :return: List of Login objects, empty list, or None
    """
    if not uri and not username:
        return None
    query_template = "SELECT LoginId, Username, Password, URI FROM Logins"
    arguments: list[str] = []
    if uri:
        query_template += " WHERE URI LIKE ?"
        arguments.append(f"%{uri}%")
    if username:
        if "WHERE" in query_template:
            query_template += " AND Username LIKE ?"
        else:
            query_template += " WHERE Username LIKE ?"
        arguments.append(f"%{username}%")
    query_template += ";"
    with access_vault(vault_path, master_password) as conn:
        if isinstance(conn, Exception):
            return None
        conn.row_factory = sqlite.Row
        cursor = conn.cursor()
        cursor.execute(query_template, arguments)
        rows: list[sqlite.Row] = cursor.fetchall()
    logins = tuple(
        Login(
            login_id=row["LoginId"],
            username=row["Username"],
            password=row["Password"],
            uri=row["URI"],
        )
        for row in rows
    )
    return logins
