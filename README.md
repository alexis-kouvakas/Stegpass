# Stegpass

A lightweight and straightforward SQLCipher-encrypted steganographic password manager and generator for enhanced security. Ideal for users seeking a secure, stylish and simple tool to manage passwords via the Linux terminal.

      This program is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.
   
      This program is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.
    
## Work in Progress!
Steganography features yet to be implemented. At the moment it is just a command-line based SQLCipher password manager!


## Example usage
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stegpass Alpha Usage Guide</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Stegpass Alpha: Example Usage</h1>
    
    <h2>Add a Password</h2>
    <pre>
        <code>python stegpass.py add vault.db example.com</code>
    </pre>

    <h2>Generate a Password</h2>
    <pre>
        <code>python stegpass.py generate vault.db example.com</code>
    </pre>

    <h2>Query a Password</h2>
    <pre>
        <code>python stegpass.py query vault.db example.com</code>
    </pre>

    <h2>Edit a Password</h2>
    <pre>
        <code>python stegpass.py edit vault.db example.com</code>
    </pre>

    <h2>Delete a Password</h2>
    <pre>
        <code>python stegpass.py delete vault.db example.com</code>
    </pre>
</body>
</html>
