from runAlg import run, get_coordinates
import os
from app import app
from flask import flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

import sqlite3

database = "frameD.db"

#format we accept
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


monitor = False
counter = 0

#DB
def writeTofile(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)
    print("Stored blob data into: ", filename, "\n")

#DB
def readBlobData(name):
    found = False
    try:
        sqliteConnection = sqlite3.connect(database)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")

        sql_fetch_blob_query = f"SELECT * FROM images WHERE KEY_NAME = ?"
        cursor.execute(sql_fetch_blob_query, (name,))
        record = cursor.fetchall()
        if record:
            found = True

        cursor.close()

    except sqlite3.Error as error:
        print("Failed to read blob data from sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("sqlite connection is closed")
            return found

#DB
def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

#DB
def insertBLOB(name, photo):
    global sqliteConnection
    try:
        sqliteConnection = sqlite3.connect(database)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        sqlite_insert_blob_query = """ INSERT INTO images
                                  (KEY_NAME, KEY_IMAGE, KEY_COORDS) VALUES (?, ?, ?)"""

        empPhoto = convertToBinaryData(photo)
        # Convert data into tuple format
        data_tuple = (name, empPhoto, "[]")
        cursor.execute(sqlite_insert_blob_query, data_tuple)
        sqliteConnection.commit()
        print("Image inserted successfully as a BLOB into images table")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("the sqlite connection is closed")

#DB
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#DB
def check_database(filename):
    file = os.path.join("images", filename)
    found_in_database = readBlobData(filename)
    if found_in_database is False:
        print("No photo found, saving to Database.")
        insertBLOB(filename, file)
    return filename

def save_coords_to_database(coords, name):
    coords_str = str(coords)
    try:
        sqliteConnection = sqlite3.connect(database)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")

        sql_fetch_blob_query = f"SELECT KEY_COORDS FROM images WHERE KEY_NAME = ?"
        cursor.execute(sql_fetch_blob_query, (name,))
        record = cursor.fetchone()
        if record is not None:
            list_of_coords = record[0]

            if len(list_of_coords) < 3:
                new_list = list_of_coords[:-1] + coords_str + "]"
            else:
                new_list = list_of_coords[:-1] +", " + coords_str + "]"

            sql_update_query = """UPDATE images set KEY_COORDS = ? where KEY_NAME = ?"""
            data = (new_list,name)
            cursor.execute(sql_update_query, data)
            sqliteConnection.commit()
            print(f"Successfully updated {coords_str} into {name} KEY_COORDS." )

        else:
            print("Problem with saving coordinates to database (record is None).")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to update KEY_COORDS data into sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("the sqlite connection is closed")

#Home page
@app.route('/')
def upload_form():
    return render_template('upload.html')

#upload image
@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        check_database(filename)
        print("file name:",filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Image successfully uploaded and displayed below')
        return render_template('uploaded.html', filename=filename)
    else:
        flash('Allowed image types are -> png, jpg, jpeg, gif')
        return redirect(request.url)
#display image
@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/run_algorithm/<filename>')
def run_algorithm(filename):
    path = run(filename)
    coords_list = get_coordinates()
    coords = []
    if coords_list is None:
        print("Problem with retrieving coordinates.")
    for coord in coords_list:
        coords.append(tuple(coord))
    return redirect(url_for('framed_pic',filename = path, coords = coords, true_file = filename))

@app.route("/framed/<filename>/<coords>/<true_file>")
def framed_pic(filename,coords, true_file):
    return render_template('framed.html', filename = filename ,coords = coords, true_file = true_file)

@app.route("/submit_frame/<coords>/<filename>")
def submit_frame(coords, filename):
    if coords is not None:
        save_coords_to_database(coords, filename)
    else:
        print("Problem with retrieving coordinates.")
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug = True,use_reloader = False)

