import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import Flask, session, render_template, request, escape, redirect, jsonify
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
    # if id_user exist render main page
    if 'id_user' in session:
        name =  session['name']
        return render_template("index.html", title="Home", name = name)
    else:
        return render_template("login/login.html", title="Login", log_message = "")

# user register layout
@app.route("/user/register")
def register_user():
    title = "New User"
    return render_template('user/register.html', title=title)
# user register method
@app.route("/user/save", methods=["post"])
def save_user():
    # Get Info.
    # Escape user inputs
    name = escape(request.form.get("name"))
    username = escape(request.form.get("username"))
    password = bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')
    # check username
    users_qry = db.execute(
        "SELECT * FROM tbl_user WHERE username = :username", {"username": username})
    if users_qry.rowcount >= 1:
        # render error message
        message = f"User {name} exists"
        return render_template('user/message.html', message=message)
    # if user doesn't exist save it
    db.execute("INSERT INTO tbl_user (name, username, password) VALUES (:name, :username, :password)",
               {"name": name, "username": username, "password": password})
    # Transaction sql
    db.commit()
    # Render success message
    message = f"User {name} saved"
    return render_template('user/message.html', message=message)


# sessions
@app.route("/login", methods=['post', 'get'])
def login():
    if request.method == 'POST':
        username = escape(request.form.get('username'))
        password = request.form.get('password')
        user = db.execute(
            'SELECT * FROM tbl_user WHERE username = :username', {"username": username}).fetchone()
        if user is None: # user doesn not found
            return render_template("login/login.html", log_message="Error login", class_ = 'alert alert-danger')
       
        if check_password_hash(user["password"], password): # check password
            # redirect home page and create session
            session['id_user'] = user["user_id"]
            session['name'] = user["name"]
            return redirect("/", code=302)
        else:
            return render_template("login/login.html", log_message="Error login", class_ = 'alert alert-danger')

    return render_template("login/login.html", title="Login", log_message = "")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/", code=302)

@app.route("/search/book", methods = ["POST"])
def search_book():
    name =  session['name']
    search = escape(request.form.get('search'))
    book = db.execute(f"SELECT * FROM tbl_books WHERE (isbn LIKE '%{search}%') OR (title LIKE '%{search}%') OR (author LIKE '%{search}%')   LIMIT 50").fetchall()

    if book is None:
        return render_template("index.html", title="Home", name = name)
    
    return render_template("index.html", title="Home", name = name, books = book)

#book page

@app.route("/book/<book_id>")
def bookPage(book_id):
    book = book_id
    result = db.execute(f"SELECT * FROM tbl_books WHERE book_id = '{book}'").fetchone()
    
    return render_template("book/book.html", title = "Book Page", books = result)


@app.route("/api/<isbn>")
def api(isbn):
    book = isbn
    result = db.execute(f"SELECT * FROM tbl_books WHERE isbn = '{book}'").fetchone()
    data = {"title":result.title,"author":result.author,"year":result.year_book, "isbn":result.isbn}
    return jsonify(data)