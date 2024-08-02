# Stegpass

A lightweight and straightforward SQLCipher-encrypted steganographic password manager and generator. Essentially lets you store and manage your passwords inside pictures for enhanced securiy. Ideal for users seeking a secure, stylish and simple tool to manage passwords via the Linux terminal.

      This program is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.
   
      This program is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.
    
## Work in Progress!
Everything is still highly experimental, don't actually use this.

## Example usage

### Add existing password
      stegpass.py add <vault.db file location> <Site ID>
### Generate password
      stegpass.py gen <vault.db file location> <Site ID>
### Edit password
      stegpass.py edit <vault.db file location> <Site ID>
### Remove password entry
      stegpass.py rem <vault.db file location> <Site ID>
### Query password entry
      stegpass.py query <vault.db file location> <Site ID>
