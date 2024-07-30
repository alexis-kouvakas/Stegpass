#  steghide .db file with marker inside .png image Done!
#  convert .jpeg/.jpg images to .png to prepare for steghide
#  best case scenario is to query directly from .png image without having to convert to .db first
#  stegunhide image to make .db file accessible
#  check for marker inside .png image to uncover database Done
#  convert binary back to .db file

import PIL.Image
import numpy as np
from PIL import Image
import os


def steghide():
    db_location = input("Enter the path to the .db file: ")
    try:
        os.path.isfile(db_location)
        with open(db_location, "rb") as file:
            binary_db = file.read()
        binary_db = ''.join(f"{byte:08b}" for byte in content)
    except Exception as e:
        print("Error:", e)
        return
    img_location = input("Enter the path to the .png file: ")
    try:
        os.path.isfile(img_location)
    except Exception as e:
        print("Error:", e)
        return
    image = PIL.Image.open(img_location, 'r')
    width, height = image.size
    img_arr = np.array(list(image.getdata()))

    if image.mode == "P":
        print("Error: Paletted images not supported. ")
        exit()

    channels = 4 if image.mode == "RGBA" else 3

    pixels = img_arr.size // channels


    indicator = b"$STEGPASS$"

    binary_db += indicator
    byte_db = ''.join(f"{ord(c):08b}" for c in binary_db)
    bits = len(byte_db)

    if bits > pixels:
        print("Error: Not enough space within image.")
    else:
        index = 0
        for i in range(pixels):
            for j in range(0, 3):
                if index < bits:
                    img_arr[i][j] = int(bin(img_arr[i][j])[2:-1] + byte_db[index], 2)
                    index += 1

    img_arr = img_arr.reshape((height, width, channels))
    result = PIL.Image.fromarray(img_arr.astype('uint8'), image.mode)
    result.save('encoded.png')


def stegunhide():
    img_location = input("Enter the path to the .png file: ")
    try:
        os.path.isfile(img_location)
        image = PIL.Image.open(img_location, 'r')
        img_arr = np.array(list(image.getdata()))
        if image.mode == "P":
            print("Error: Paletted images not supported. ")
            exit()
        channels = 4 if image.mode == "RGBA" else 3
        pixels = img_arr.size // channels

        secret_bits = [bin(img_arr[i][j])[-1] for i in range(pixels) for j in range(0,3)]
        secret_bits = ''.join(secret_bits)
        secret_bits = [secret_bits[i:i+8] for i in range(0, len(secret_bits), 8)]

        database = [chr(int(secret_bits[i], 2)) for i in range(len(secret_bits))]
        database = ''.join(database)
        indicator = "$STEGPASS$"

        if indicator in database:
            db_content = database[:database.index(indicator)]
            with open('decrypted.db', "wb") as file:
                file.write(db_content.encode())
        else:
            print('Error: No database found.')
    except Exception as e:
        print('Error:', e)
        return

steghide()
stegunhide()