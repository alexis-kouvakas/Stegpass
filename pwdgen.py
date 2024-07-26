import string
import secrets

def main():

    strlength = input('How many characters long should the password be? ')
    length = int(strlength)
    pwdgen(length)
    
def pwdgen(length):
    letters = list(string.ascii_letters)
    digits = list(string.digits)
    symbols = list(string.punctuation)
    charlist = list(letters + digits + symbols)
    password = []
    i = 0
    while i < length:
        password.append(secrets.choice(charlist))
        i += 1
    password = ''.join(password)
    print("Generated Password:", password)




main()
