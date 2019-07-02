import os
from os.path import join, dirname
from dotenv import load_dotenv
import requests

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
        name = session['name']
        return render_template("index.html", title="Home", name=name)
    else:
        return render_template("login/login.html", title="Login", log_message="")

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
    password = bcrypt.generate_password_hash(
        request.form.get("password")).decode('utf-8')
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
        if user is None:  # user doesn not found
            return render_template("login/login.html", log_message="Error login", class_='alert alert-danger')

        if check_password_hash(user["password"], password):  # check password
            # redirect home page and create session
            session['id_user'] = user["user_id"]
            session['name'] = user["name"]
            return redirect("/", code=302)
        else:
            return render_template("login/login.html", log_message="Error login", class_='alert alert-danger')

    return render_template("login/login.html", title="Login", log_message="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/", code=302)


@app.route("/search/book", methods=["POST"])
def search_book():
    name = session['name']
    search = escape(request.form.get('search'))
    book = db.execute(
        f"SELECT * FROM tbl_books WHERE (isbn LIKE '%{search}%') OR (title LIKE '%{search}%') OR (author LIKE '%{search}%')   LIMIT 50").fetchall()

    if book is None:
        return render_template("index.html", title="Home", name=name)

    return render_template("index.html", title="Home", name=name, books=book)

# book page


@app.route("/book/<book_id>")
def bookPage(book_id):

    if 'id_user' in session:
        name = session['name']
        book = book_id
        result = db.execute(
            f"SELECT * FROM tbl_books WHERE book_id = '{book}'").fetchone()
        if result is None:
            return render_template("book/message.html", title="Error", message="No Book")
        rateB = db.execute(
            f"SELECT tbl_reviews.rate as rate, tbl_reviews.review as review, tbl_user.username as user  FROM tbl_reviews LEFT JOIN tbl_user ON tbl_reviews.user_id = tbl_user.user_id WHERE book_id = '{book}' ")
        average = db.execute("SELECT AVG(rate) as res FROM tbl_reviews WHERE book_id = :book_id", {
            "book_id": book}).fetchone()
        review_count = db.execute(
            "SELECT COUNT(*) as total FROM tbl_reviews WHERE book_id = :book_id", {"book_id": book}).fetchone()
        # goodreads api
        goodreads = requests.get("https://www.goodreads.com/book/review_counts.json",
                                 params={"key": "rauBKNbB4l5F65wSw8CoWg", "isbns": result.isbn})
        if rateB.rowcount >= 1:
            return render_template("book/book.html", title="Book Page", goodreads=goodreads.json(), name=name, books=result, reviews=rateB, average=float(average.res), review_count=int(review_count.total))
        return render_template("book/book.html", title="Book Page", name=session['name'], books=result, average=0, review_count=0, goodreads=goodreads.json())
    else:
        return render_template("login/login.html", title="Login", log_message="You must be logged", class_='alert alert-danger')


# Rate & Review Methods


@app.route('/review/save', methods=['POST'])
def review():
    if request.method == "POST":
        book = request.form.get('id_book')
        user = session['id_user']
        rate = request.form.get('rate')
        review = escape(request.form.get('review'))

        # verify user has not rated before
        rateB = db.execute(
            f"SELECT * FROM tbl_reviews WHERE (user_id = '{user}') AND (book_id = '{book}')")
        if rateB.rowcount >= 1:
            return render_template("book/message.html", title="Error", message="User already rated this book")
        # Proceed to save review
        db.execute("INSERT INTO tbl_reviews (book_id, user_id, rate, review) VALUES (:book_id, :user_id, :rate, :review)",
                   {"book_id": int(book), "user_id": user, "rate": int(rate), "review": review})
        # Transaction sql
        db.commit()
        return render_template("book/message.html", title="Success", message="Done")
# API Application


@app.route("/api/<isbn>")
def api(isbn):
    book = isbn
    result = db.execute(
        f"SELECT * FROM tbl_books WHERE isbn = '{book}'").fetchone()
    if result is None:
        return 'Error 404'
    # average and count reviews
    average = db.execute("SELECT AVG(rate) as res FROM tbl_reviews WHERE book_id = :book_id", {
                         "book_id": result.book_id}).fetchone()
    review_count = db.execute(
        "SELECT COUNT(*) as total FROM tbl_reviews WHERE book_id = :book_id", {"book_id": result.book_id}).fetchone()

    if average.res is None:
        data = {"title": result.title, "author": result.author,
                "year": result.year_book, "isbn": result.isbn,
                "average": 0, "review_count": 0}
    else:
        data = {"title": result.title, "author": result.author,
                "year": result.year_book, "isbn": result.isbn,
                "average": float(average.res), "review_count": review_count.total}
    # float(average.fetchone().res)""
    return jsonify(data)


# 404
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return 'Error 404', 404
