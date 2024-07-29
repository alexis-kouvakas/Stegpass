import os
import string
import secrets
import pyperclip
import typer
from typing_extensions import Annotated
from pysqlcipher3 import dbapi2 as sqlite
from getpass import getpass

app = typer.Typer()

@app.command()
def connect(vault_path: Annotated[str, typer.Argument()] = "vault.db"):    # Connects to an existing vault or creates a new one
    new_vault = not os.path.exists(vault_path)

    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()

    if new_vault:
        print("Vault does not exist. Creating a new vault.")
        vault_key = getpass("Enter a new vault key:\n")
    else:
        vault_key = getpass("Password:\n")

    cursor.execute(f"PRAGMA key = '{vault_key}'")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS passwords (vault_id text, username text, password text)"
    )
    connection.commit()
    connection.close()

    if new_vault:
        print(f"New vault created")
    else:
        print(f"Vault loaded successfully")


@app.command()
def add_pwd():
    vault_id = input("ID:\n")
    username = input("Username:\n")
    password = getpass("Password:\n")
    if len(password) < 7:
        print('Invalid number. Length must be > 6.')
        return
    else:
        save_pwd(vault_id, username, password)

@app.command()
def generate_pwd():  # Generates a secure password and copies it to the clipboard
    letters = list(string.ascii_letters)
    digits = list(string.digits)
    symbols = list(string.punctuation)
    char_list = list(letters + digits + symbols)
    password = []
    vault_id = input('ID:\n')
    username = input('Username:\n')
    while True:
        try:
            length = int(input('How many characters long should the password be? (min. 7):\n'))
            if length > 6:
                break
            else:
                print('Invalid number. Length must be > 6.')
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
    save_pwd(vault_id, username, password)

@app.command()
def query_pwd():
    id_input = input('ID:\n')
    username = input('Username:\n')
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    vault_key = getpass("Password:\n")
    cursor.execute(f"PRAGMA key = '{vault_key}'")
    cursor.execute('SELECT password FROM passwords WHERE vault_id = ? AND username = ?', (id_input, username))
    password = cursor.fetchone()[0]
    connection.close()
    if password:
        print('Password copied to clipboard!' )
        pyperclip.copy(password)
    else:
        print('No password found for', id_input)
        return None


def save_pwd(vault_id, username, password):
    save = input()
    while True:
        if save == 'y':
            connection = sqlite.connect(vault_path)
            cursor = connection.cursor()
            vault_key = getpass("Password:\n")
            cursor.execute(f"PRAGMA key = '{vault_key}'")
            cursor.execute("INSERT INTO passwords VALUES (?, ?, ?)", (vault_id, username, password))
            connection.commit()
            connection.close()
            print("Password saved.")
            break
        elif save == 'n':
            print("Password not saved.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            save_pwd(password, vault_id, username)


if __name__ == "__main__":
    app()