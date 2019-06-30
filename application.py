import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import Flask, session, render_template, request
from flask_session import Session
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
# hash passwords
bcrypt = Bcrypt(app)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"

# user register layout
@app.route("/user/register")
def register_user():
    title = "New User"
    return render_template('user/register.html', title=title)
# user register method
@app.route("/user/save", methods=["post"])
def save_user():
    # Get Info.
    name = request.form.get("name")
    username = request.form.get("username")
    password = bcrypt.generate_password_hash(request.form.get("password"))
    # check username
    if db.execute("SELECT * FROM tbl_user WHERE username = :username", {"username": username}).rowcount >= 1:
        message = f"User {name} exists"
        return render_template('user/message.html', message=message)
    db.execute("INSERT INTO tbl_user (name, username, password) VALUES (:name, :username, :password)",
               {"name": name, "username": username, "password": password})
    db.commit()
    message = f"User {name} saved"
    return render_template('user/message.html', message=message)
