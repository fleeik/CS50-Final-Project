import os
from os.path import join, dirname, realpath
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_from_directory, url_for
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image

from helpers import apology, login_required

app = Flask(__name__)

UPLOAD_FOLDER = "/home/ubuntu/project/static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    # Check and confirm proper register usage.
    if request.method == "POST":

        # Check for bad inputs.
        if not request.form.get("username"):
            return apology("One does not simply register without a username.")
        elif not request.form.get("psw"):
            return apology("One does not simply register without a psw.")
        elif not request.form.get("pswc"):
            return apology("One does not simply register without a correct password confirmation")
        elif not request.form.get("country"):
            return apology("One does not simply register without a country.")
        elif not request.form.get("background"):
            return apology("One does not simply register without a background.")

        elif request.form.get("psw") != request.form.get("pswc"):
            return apology("One does not simply register without a password confirmation")

        # TODO Check if user already exists in database.
        rows = db.execute("SELECT * FROM users WHERE name = :username",
                     username=request.form.get("username"))
        if len(rows) == 1:
            return apology("Ones does not simply copy someone else.")

        # variable requests.
        un = request.form.get("username")
        psw = request.form.get("psw")
        ctry = request.form.get("country")
        bg = request.form.get("background")
        image = request.form.get("image")
        date = datetime.now()
        year = date.strftime("%Y")

        # Hash password.
        hpsw = generate_password_hash(psw)

        #image to static
        file = request.files['image']
        filename = str(un)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename + '.jpg'))


        # SQL Injection.
        db.execute("INSERT INTO users (name, psw, country, background, pict, since) VALUES (?, ?, ?, ?, ?, ?)", un, hpsw, ctry, bg, image, year)

        return redirect("/success")

    else:
        return render_template("register.html")

@app.route("/lounge")
@login_required
def lounge():

        data = db.execute("SELECT * FROM posting JOIN users ON users.id=posting.user_id ORDER BY post_id;")
        replies = db.execute("SELECT * FROM replies;")
        return render_template("lounge.html", data=data, replies=replies)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("psw"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["psw"], request.form.get("psw")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/profile/<n>")
@login_required
def profile(n):

    #Query Database.
    user_name = n
    query = db.execute("SELECT * FROM users WHERE name=:name", name=user_name)
    for i in query:
        name = i['name']
        ubication = i['country']
        posts = i['posts']
        background = i['background']

    return render_template("profile.html", name=name, ubication=ubication, posts=posts, background=background)

@app.route("/success")
def success():
    session.clear()
    return render_template("success.html")

@app.route("/posting", methods=["GET", "POST"])
@login_required
def posting():

    if request.method == "POST":

        post = str(request.form.get("post"))
        user_id = session.get("user_id")

        # Query posts and sum 1
        query = db.execute("SELECT posts FROM users WHERE id=:user_id;", user_id=user_id)
        for i in query:
            nposts = i['posts']
            if nposts == None:
                nposts = 0
                nposts = nposts + 1
            else:
                nposts = nposts + 1

        #SQL inject
        db.execute("INSERT INTO posting (user_id, post) VALUES (?, ?);", user_id, post)
        db.execute("UPDATE users SET posts=? WHERE id=?", nposts, user_id)

        return redirect("/lounge")

    else:
        return render_template("post.html")

@app.route("/reply/<int:id>", methods=["GET", "POST"])
@login_required
def reply(id):

        if request.method == "POST":
            post_id = id
            post = request.form.get("reply")
            user_id = session.get("user_id")
            user_name = db.execute("SELECT name FROM users WHERE id =:user_id", user_id=user_id)
            for e in user_name:
                user = e['name']
            db.execute("INSERT INTO replies (usern, id_post, reply) VALUES (?, ?, ?)", user, post_id, post)
            return redirect("/lounge")

        else:
            post_id = id
            return render_template("reply.html", post_id=post_id)


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


@app.route("/likes", methods=["GET", "POST"])
def likes():

    if request.method == "POST":
        post_id = int(request.form.get("lbutton"))
        likes = db.execute("SELECT likes FROM posting WHERE post_id=?", post_id)
        for i in likes:
            clikes = i['likes']
            if clikes == None:
                clikes = 0
                clikes = clikes + 1
            else:
                clikes = clikes + 1

        #SQL Injeection
        db.execute("UPDATE posting SET likes=? WHERE post_id=?", clikes, post_id)

        return redirect("lounge")
    else:
        return redirect("/lounge")



