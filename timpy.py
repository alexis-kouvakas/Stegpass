import string
import secrets
import pyperclip
from argon2 import PasswordHasher
import glob


def genpaswd():
    letters = list(string.ascii_letters)
    digits = list(string.digits)
    symbols = list(string.punctuation)
    charlist = list(letters + digits + symbols)
    password = []

    while True:
        try:
            length = int(input('How many characters long should the password be? (Min. 7):\n'))
            if length > 6:
                break
            else:
                print('Invalid number. Length must be > 6')
        except ValueError:
            print('Invalid input. Length must be an integer')

    password.append(secrets.choice(digits))
    password.append(secrets.choice(symbols))
    for i in range(length - 2):
        password.append(secrets.choice(charlist))
    secrets.SystemRandom().shuffle(password)
    password = ''.join(password)
    return password


def newvault():
    letters = list(string.ascii_letters)
    digits = list(string.digits)
    alphanumcharlist = list(letters + digits)
    vaultid = []
    for i in range(20):
        vaultid.append(secrets.choice(alphanumcharlist))
    vaultid = ''.join(vaultid)
    filename = f"{vaultid}.txt"
    ph = PasswordHasher()
    vaultkeyhashed = ph.hash(str(input('Enter your new vault.txt key:\n')))
    with open(filename, "w") as file:
        file.write(f'vaultkey: {vaultkeyhashed}\n')


def managevault():
    for filename in glob.glob("*.txt"):
        ph = PasswordHasher()
        pwdinput = input('Enter your vault.txt key:\n')
        with open(filename, "r") as file:
            content = file.read()
            if 'vaultkey: ' in content:
                stored_hash = content.split('vaultkey: ')[1].strip()

                try:
                    ph.verify(stored_hash, pwdinput)
                    print('Login successful!')
                    return
                except Exception as e:
                    print('Wrong password! Error:', e)
            else:
                print('Invalid vault file format!')


def main():
    print("""Welcome to Timpy v0.1!

    1.) Manage an existing vault.txt
    2.) Create a new vault.txt
    3.) Exit
    """)

    menupoint = int(input())
    if menupoint == 1:
        managevault()
    elif menupoint == 2:
        newvault()
        main()
    elif menupoint == 3:
        exit()

if __name__ == "__main__":
    main()
