import secrets
import string
import subprocess
from getpass import getpass
from typing import Annotated, NoReturn
from pathlib import Path

import pyperclip
import typer

import stegpass.database as steg_db
from stegpass.database_queries import LoginQuery
from stegpass.database_structures import Login

app = typer.Typer()


@app.command()
def init(vault_path: Annotated[Path, typer.Argument()]) -> NoReturn:
    if vault_path.exists():
        print(f"File already exists at {vault_path}")
        raise typer.Exit(code=1)
    else:
        print("Confirmed that vault does not exist, creating a new vault")
        master_password = getpass("Enter a new master password:\n")
        success = steg_db.create_vault(vault_path, master_password)
        if success:
            print(f"Sucessfully created vault at {vault_path}")
        else:
            print(f"Failed to create vault at {vault_path}")
        raise typer.Exit()


@app.command()
def add(
    vault_path: Annotated[Path, typer.Argument()],
    uri: Annotated[str, typer.Argument()],
    username: Annotated[str, typer.Argument()],
) -> NoReturn:
    if not vault_path.exists():
        print("Vault does not exist. Use the init command to create one.")
        raise typer.Exit(code=1)
    while True:
        password = getpass(f"Enter the password for {username}: ")
        if len(password) >= 7:
            master_password = getpass("Master password: ")
            success = steg_db.save_login(
                vault_path,
                master_password,
                LoginQuery(username, password, uri)
            )
            if success is None:
                print("Failed to access database.")
                raise typer.Exit(code=1)
            elif success:
                print(f"Successfully saved password for {username}")
                raise typer.Exit()
            else:
                print(f"Failed to save password for {username}")
                raise typer.Exit(code=1)

        else:
            print('Invalid length. (Min: 7)')


@app.command()
def gen(
    vault_path: Annotated[Path, typer.Argument()],
    uri: Annotated[str, typer.Argument()],
    username: Annotated[str, typer.Argument()],
) -> NoReturn:
    if not vault_path.exists():
        print("Vault does not exist. Use the init command to create one.")
        raise typer.Exit(code=1)
    letters = list(string.ascii_letters)
    digits = list(string.digits)
    symbols = list(string.punctuation)
    char_list = list(letters + digits + symbols)
    password = []
    while True:
        try:
            length = int(input(
                'How many characters long should '
                'the password be? (min. 7): '
            ))
            if length > 6:
                break
            else:
                print('Invalid length. (Min: 7)')
        except ValueError:
            print('Invalid input. Length must be an integer.')

    password.append(secrets.choice(digits))
    password.append(secrets.choice(symbols))
    for i in range(length - 2):
        password.append(secrets.choice(char_list))
    secrets.SystemRandom().shuffle(password)
    password = ''.join(password)
    pyperclip.copy(password)
    print('Your new password has been copied to the clipboard!')
    master_password = getpass("Master password:")
    success = steg_db.save_login(
        vault_path,
        master_password,
        LoginQuery(username, password, uri)
    )
    if success:
        print(f"Successfully saved password for {username}")
        raise typer.Exit()
    else:
        print(f"Failed to save password for {username}")
        raise typer.Exit(code=1)


@app.command()
def query(
    vault_path: Annotated[Path, typer.Argument()],
    uri: Annotated[str, typer.Option()] = "",
    username: Annotated[str, typer.Option()] = "",
) -> NoReturn:
    if not vault_path.exists():
        print("Vault does not exist. Use the init command to create one.")
        raise typer.Exit(code=1)
    if uri == "" and username == "":
        print("You need to specify a username or URI")
        raise typer.Exit(code=1)
    master_password = getpass("Master Password: ")
    login = query_login_interactive(
        vault_path, master_password, uri=uri, username=username
    )
    # TODO Handle finding multiple logins
    pyperclip.copy(login.password)
    print(f'Password for {login.username} ({login.uri}) copied to clipboard!')
    raise typer.Exit()


@app.command()
def edit(
    vault_path: Annotated[Path, typer.Argument()],
    uri: Annotated[str, typer.Option()] = "",
    username: Annotated[str, typer.Option()] = "",
) -> NoReturn:
    if not vault_path.exists():
        print("Vault does not exist. Use the init command to create one.")
        raise typer.Exit(code=1)
    master_password = getpass("Master password: ")
    login = query_login_interactive(
        vault_path, master_password, uri=uri, username=username
    )
    while True:
        password = getpass("New password: ")
        if len(password) >= 7:
            with steg_db.access_vault(vault_path, master_password) as conn:
                assert not isinstance(conn, Exception)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE Logins SET Password = ? WHERE LoginId = ?',
                    (password, login.login_id),
                )
                cursor.close()
                conn.commit()
            print("Password updated.")
            raise typer.Exit()
        else:
            print('Invalid length. (Min > 6.)')


@app.command()
def rem(
    vault_path: Annotated[Path, typer.Argument()],
    uri: Annotated[str, typer.Option()] = "",
    username: Annotated[str, typer.Option()] = "",
) -> NoReturn:
    if not vault_path.exists():
        print("Vault does not exist. Use the init command to create one.")
        raise typer.Exit(code=1)
    master_password = getpass("Master Password: ")
    login = query_login_interactive(
        vault_path, master_password, uri=uri, username=username
    )
    confirm = input(
        "Are you sure you want to delete the entry for "
        f"{login.username} ({login.uri})? (y/N): "
    )
    with steg_db.access_vault(vault_path, master_password) as conn:
        assert not isinstance(conn, Exception)
        cursor = conn.cursor()
        if confirm.lower() == 'y':
            cursor.execute(
                'DELETE FROM Logins WHERE LoginId = ?',
                (login.login_id,)
            )
            cursor.close()
            conn.commit()
            print("Entry deleted.")
        else:
            print("Deletion cancelled.")
    raise typer.Exit()


def query_login_interactive(
    vault_path: Path,
    master_password: str,
    *,
    uri: str | None = None,
    username: str | None = None,
) -> Login:
    """Ask the user if multiple logins are found, else return the only login.

    This function will exit the program if either the password is incorrect
    or if no logins are returned.

    :param vault_path: Path to the vault database file
    :param master_password: Password to unlock the vault with
    :param uri: The URI to match in the Logins table
    :param username: The Username to match in the logins table
    :return: Login object
    """
    if uri == "" and username == "":
        print("You need to specify a username or URI")
        raise typer.Exit(code=1)
    logins = steg_db.get_logins_by_query(
        vault_path, master_password, uri=uri, username=username,
    )
    if logins is None:
        print("Error while accessing database")
        raise typer.Exit(code=1)
    if not logins:
        print("No logins match the details provided")
        raise typer.Exit(code=1)
    if len(logins) > 1:
        max_id_len: int = 5  # Starts at 5 because of the word "Index"
        max_username_len: int = 8  # len("Username") == 8
        max_uri_len: int = 3  # len("URI") == 3
        for login in logins:
            max_id_len = max(len(str(login.login_id)), max_id_len)
            max_username_len = max(len(str(login.username)), max_username_len)
            max_uri_len = max(len(str(login.uri)), max_uri_len)
        format_template = (
            f"| {{:^{max_id_len}}} | {{:<{max_username_len}}} "
            f"| {{:<{max_uri_len}}} |"
        )
        print("Found the following logins")
        print("\n")
        print(format_template.format("Index", "Username", "URI"))
        for index, login in enumerate(logins):
            print(
                format_template.format(
                    index + 1,
                    login.username,
                    login.uri or ""
                )
            )
        while True:
            index = input(
                "Select an index with the associated login "
                "(q to quit): "
            )
            if index.lower() == "q":
                raise typer.Exit()
            else:
                try:
                    login = logins[int(index) - 1]
                    break
                except ValueError:
                    print("The index needs to be an integer")
                except IndexError:
                    print("That is not a valid index")
    else:
        login = logins[0]
    print(f"Found login for {login.username} at {login.uri}")
    return login


def run_steghide_command(
    command,
    input_file=None,
    output_file=None,
    password=None
):  # EXPERIMENTAL/UNTESTED DON'T TRY OUT ON A DATABASE YOU CARE ABOUT
    cmd = ['steghide', command]

    if input_file:
        cmd.extend(['-cf', input_file])
    if output_file:
        cmd.extend(['-of', output_file])
    if password:
        cmd.extend(['-p', password])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.CalledProcessError as e:
        stdout = e.stdout
        stderr = e.stderr

    return stdout, stderr


def embed(vault_key, vault_path, carrier_file):
    output, error = run_steghide_command(
        'embed',
        input_file=vault_path,
        output_file=carrier_file,
        password=vault_key,
    )
    print("Embed Output:", output)
    print("Embed Error:", error)


def extract(vault_key, vault_path):
    output, error = run_steghide_command(
        'extract',
        input_file=vault_path,
        output_file='vault.db',
        password=vault_key
    )
    print("Extract Output:", output)
    print("Extract Error:", error)


if __name__ == "__main__":
    app()
