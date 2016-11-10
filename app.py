from flask import Flask, request
import sqlite3
import hashlib
import uuid

database = '/Ebay.db'
app = Flask(__name__)
# public functions
@app.route('/register', methods=['POST'])
def register():
    conn = sqlite3.connect('users.db')
    # on post request add the username and password to the database
    if request.method == 'POST':
        tup = _saltHash(request.form['password'])
        hashedPassword = tup[0]
        salt = tup[1]
        cursor = conn.execute("INSERT INTO Users VALUES (NULL, ? , ? , ? , ? , ?)", (request.form['username'], hashedPassword, salt, request.form['isBuyer'], request.form['isSeller']))
        conn.commit()
        conn.close()
        return ""

@app.route('/login', methods=['POST'])
def login():
    conn = sqlite3.connect('users.db')
    return _authenticate(request.form['username'], request.form['password'], conn)

# private functions
def _saltHash(password):
    salt = uuid.uuid4().hex
    hashed_password = hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
    return (hashed_password, salt)

def _authenticate(username, password, conn):
    cursor = conn.execute("SELECT salt FROM Users WHERE username= ? ", (username,))
    for row in cursor:
        salt = row[0]
    saltedPassword = password.encode('utf-8') + salt.encode('utf-8')
    cursor = conn.execute("SELECT *  FROM Users WHERE username=? AND password=?", (username, hashlib.sha512(saltedPassword).hexdigest()))
    data = cursor.fetchall()
    if len(data)==0:
        return "0"
    else:
        return "1"

if __name__ == '__main__':
    app.run
