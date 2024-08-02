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
def init():
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
        connection.close()
    else:
        print('Error: File not found.')
        connection.close()
        exit()


@app.command()
def add(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    if new_vault:
        print("Vault does not exist. Use the init command to create one.")
        exit()
    else:
        print("Vault found.\n")
    vault_id = id_input
    while True:
        password = getpass("Password:\n")
        if len(password) >= 7:
            save_pwd(vault_id, password, vault_path)
            break

        else:
            print('Invalid length. (Min: 7)')


@app.command()
def gen(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    if new_vault:
        print("Vault does not exist. Use the init command to create one.")
        exit()
    else:
        print("Vault found.\n")
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
    save_pwd(vault_id, password, vault_path)

@app.command()
def query(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    if new_vault:
        print("Vault does not exist. Use the init command to create one.")
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

@app.command()
def edit(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
    new_vault = not os.path.exists(vault_path)
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    if new_vault:
        print("Vault does not exist. Use the init command to create one.")
        exit()
    else:
        cursor.execute('SELECT vault_id FROM passwords WHERE vault_id = ?', (id_input,))
        entry = cursor.fetchone()[0]
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
def rem(vault_path: Annotated[str, typer.Argument()] = "vault.db", id_input: str = typer.Argument(..., help="The ID of the site to query.")):
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
            connection.commit()
            print("Entry deleted.")
        else:
            print("Deletion cancelled.")
    connection.close()

def save_pwd(vault_id, password, vault_path):
    connection = sqlite.connect(vault_path)
    cursor = connection.cursor()
    save = input("Do you want to save the password to your vault? (y/n):\n")
    vault_key = getpass('Master password:\n')
    while True:
        if save == 'y':
            cursor.execute(f"PRAGMA key = '{vault_key}'")
            cursor.execute("INSERT INTO passwords VALUES (?, ?)", (vault_id, password))
            connection.commit()
            connection.close()
            print("Password saved.")
        elif save == 'n':
            print("Password not saved.")
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            save_pwd(password, vault_id, vault_path)

def run_steghide_command(command, input_file=None, output_file=None, password=None): # EXPERIMENTAL/UNTESTED DON'T TRY OUT ON A DATABASE YOU CARE ABOUT
    cmd = ['steghide', command]

    if input_file:
        cmd.extend(['-cf', input_file])
    if output_file:
        cmd.extend(['-of', output_file])
    if password:
        cmd.extend(['-p', password])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.CalledProcessError as e:
        stdout = e.stdout
        stderr = e.stderr

    return stdout, stderr

def embed(vault_key, vault_path):
    output, error = run_steghide_command('embed', input_file=vault_path, output_file=carrier_file,
                                        password=vault_key)
    print("Embed Output:", output)
    print("Embed Error:", error)

def extract(vault_key, vault_path):
    output, error = run_steghide_command('extract', input_file=vault_path, output_file='vault.db',
                                        password=vault_key)
    print("Extract Output:", output)
    print("Extract Error:", error)


if __name__ == "__main__":
    app()
