import os
import string
import secrets
import pyperclip
import typer
from typing_extensions import Annotated
from pysqlcipher3 import dbapi2 as sqlite
from getpass import getpass
import subprocess

app = typer.Typer()


@app.command()
def add(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    if new_vault:
        print("Vault does not exist. Creating a new vault.")
        vault_key = getpass("Enter a new master password:\n")
        cursor.execute(f"PRAGMA key = '{vault_key}'")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS passwords (vault_id text, password text)"
        )
    else:
        print("Vault found.\n")
        vault_key = getpass("Master Password:\n")
        try:
                cursor.execute(f"PRAGMA key = '{vault_key}'")
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS passwords (vault_id text, password text)"
                )
        except Exception as e:
                print(f"Error verifying password: {e}")
                exit()
    vault_id = id_input
    while True:
        password = getpass("Password:\n")
        if len(password) >= 7:
            save_pwd(vault_id, password, vault_path, vault_key)
            break

        else:
            print('Invalid length. (Min: 7)')


@app.command()
def generate(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    if new_vault:
        print("Vault does not exist. Creating a new vault.")
        vault_key = getpass("Enter a new master password:\n")
        cursor.execute(f"PRAGMA key = '{vault_key}'")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS passwords (vault_id text, password text)"
        )
    else:
        print("Vault found.\n")
        vault_key = getpass("Master Password:\n")
        try:
            cursor.execute(f"PRAGMA key = '{vault_key}'")
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS passwords (vault_id text, password text)"
            )
        except Exception as e:
            print(f"Error verifying password: {e}")
            exit()
    letters = list(string.ascii_letters)
    digits = list(string.digits)
    symbols = list(string.punctuation)
    char_list = list(letters + digits + symbols)
    password = []
    vault_id = id_input
    while True:
        try:
            length = int(input('How many characters long should the password be? (min. 7):\n'))
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
    save_pwd(vault_id, password, vault_path, vault_key)

@app.command()
def query(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    if new_vault:
        print("Vault does not exist.")
        exit()
    else:
        print("Vault found.\n")
        vault_key = getpass("Master Password:\n")
        try:
            cursor.execute(f"PRAGMA key = '{vault_key}'")
        except Exception as e:
            print(f"Error verifying password: {e}")
            exit()
    cursor.execute('SELECT password FROM passwords WHERE vault_id = ?', (id_input,))
    password = cursor.fetchone()[0]
    connection.close()
    if password:
        print('Password copied to clipboard!' )
        pyperclip.copy(password)
    else:
        print('No password found for', id_input)
        return None

@app.command()
def edit(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    cursor.execute('SELECT vault_id FROM passwords WHERE vault_id = ?', (id_input,))
    entry = cursor.fetchone()[0]
    if new_vault:
        print("Vault does not exist.")
        exit()
    else:
        if entry:
            print('Entry found for', id_input)
        else:
            print('No entry found for', id_input)
            connection.close()
            exit()
        print("Vault found.\n")
        vault_key = getpass("Master Password:\n")
        try:
            cursor.execute(f"PRAGMA key = '{vault_key}'")
        except Exception as e:
            print(f"Error verifying password: {e}")
            exit()
    while True:
        password = getpass("New password:\n")
        if len(password) >= 7:
            cursor.execute('UPDATE passwords SET password = ? WHERE vault_id = ?', (password, id_input))
            print("Password updated.")
            break

        else:
            print('Invalid length. (Min > 6.)')
    connection.commit()
    connection.close()

@app.command()
def delete(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    if new_vault:
        print("Vault does not exist.")
        exit()
    else:
        print("Vault found.\n")
        vault_key = getpass("Master Password:\n")
        try:
            cursor.execute(f"PRAGMA key = '{vault_key}'")
        except Exception as e:
            print(f"Error verifying password: {e}")
            exit()
        cursor.execute('SELECT vault_id FROM passwords WHERE vault_id = ?', (id_input,))
        entry = cursor.fetchone()[0]
        if entry:
            print('Entry found for', id_input)
        else:
            print('No entry found for', id_input)
            connection.close()
            exit()
        confirm = input(f"Are you sure you want to delete the password for {id_input}? (y/n):\n")
        if confirm.lower() == 'y':
            cursor.execute('DELETE FROM passwords WHERE vault_id = ?', (id_input,))
            print("Entry deleted.")
        else:
            print("Deletion cancelled.")

    connection.commit()
    connection.close()

def save_pwd(vault_id, password, vault_path, vault_key):
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    save = input("Do you want to save the password to your vault.db? (y/n):\n")
    while True:
        if save == 'y':
            cursor.execute(f"PRAGMA key = '{vault_key}'")
            cursor.execute("INSERT INTO passwords VALUES (?, ?)", (vault_id, password))
            connection.commit()
            connection.close()
            print("Password saved.")
            break
        elif save == 'n':
            print("Password not saved.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            save_pwd(password, vault_id)


if __name__ == "__main__":
    app()
