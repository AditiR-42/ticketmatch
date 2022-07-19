import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from datetime import date
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database
db = SQL("sqlite:///match.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def home():
    # POST
    if request.method == "POST":
        if session.get("user_id") is None:
            return render_template("login.html") 
        else:
            # Insert sale item into transactions
            eventid = request.form.get("id")
            events = db.execute("SELECT event FROM items WHERE id = ?", eventid)
            event = events[0]['event']
            types = db.execute("SELECT type FROM items WHERE id=?", eventid)
            type = types[0]['type']
            prices = db.execute("SELECT price FROM items WHERE id=?", eventid)
            price = prices[0]['price']
            quantities = db.execute("SELECT quantity FROM items WHERE id=?", eventid)
            quantity = quantities[0]['quantity']
            db.execute("""INSERT INTO transactions (user_id, type, transaction_type, event, quantity, price) VALUES (?, ?, ?, ?, ?, ?)""",
                session["user_id"], type, "Purchase", event, quantity, price)
            flash("Offer submitted!")
            return redirect("/profile") 
              
    else:
        # Render homepage
        items = db.execute("SELECT * FROM items WHERE date > ?", date.today())
        return render_template("home.html", items=items)

@app.route("/rideshares", methods=["GET", "POST"])
def rideshares():
    #POST
    if request.method == "POST":
        # Ensure user is logged in before the submit an offer
        if session.get("user_id") is None:
            return render_template("login.html") 
        else:
            # Insert item into transactions
            eventid = request.form.get("id")
            events = db.execute("SELECT event FROM items WHERE id = ?", eventid)
            event = events[0]['event']
            types = db.execute("SELECT type FROM items WHERE id=?", eventid)
            type = types[0]['type']
            prices = db.execute("SELECT price FROM items WHERE id=?", eventid)
            price = prices[0]['price']
            quantities = db.execute("SELECT quantity FROM items WHERE id=?", eventid)
            quantity = quantities[0]['quantity']
            db.execute("""INSERT INTO transactions (user_id, type, transaction_type, event, quantity, price) VALUES (?, ?, ?, ?, ?, ?)""",
                session["user_id"], type, "Purchase", event, quantity, price)
            flash("Offer submitted!")
            return redirect("/profile") 
              
    else:
        # Render homepage
        rides = db.execute("SELECT * FROM items WHERE date > :date AND type='ride'", date=date.today())
        return render_template("rideshares.html", rides=rides)


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # Get username
    username = request.args.get("username")

    # Check for username
    if not len(username) or db.execute("SELECT 1 FROM users WHERE username = :username", username=username):
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/profile")
@login_required
def profile():
    # Create table of transactions to be displayed in user profile
    userinfo = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])  
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = :user_id", user_id=session["user_id"])  
    return render_template("profile.html", userinfo=userinfo, transactions=transactions)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    # Forget any user_id
    session.clear()

    # Redirect user to homepage
    return redirect("/")


@app.route("/tickets", methods=["GET", "POST"])
def tickets():
    # POST
    if request.method == "POST":
        # Ensure user is logged in before they submit an offer
        if session.get("user_id") is None:
            return render_template("login.html") 
        else:
            # Insert item into transactions
            eventid = request.form.get("id")
            events = db.execute("SELECT event FROM items WHERE id = ?", eventid)
            event = events[0]['event']
            types = db.execute("SELECT type FROM items WHERE id=?", eventid)
            type = types[0]['type']
            prices = db.execute("SELECT price FROM items WHERE id=?", eventid)
            price = prices[0]['price']
            quantities = db.execute("SELECT quantity FROM items WHERE id=?", eventid)
            quantity = quantities[0]['quantity']
            db.execute("""INSERT INTO transactions (user_id, type, transaction_type, event, quantity, price) VALUES (?, ?, ?, ?, ?, ?)""",
                session["user_id"], type, "Purchase", event, quantity, price)
            flash("Offer submitted!")
            return redirect("/profile") 
                   
    else:
        # Render homepage
        tickets = db.execute("SELECT * FROM items WHERE date > :date AND type='ticket'", date=date.today())
        return render_template("tickets.html", tickets=tickets)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for an account."""

    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # Add user to database
        try:
            id = db.execute("INSERT INTO users (username, hash, firstname, lastname) VALUES(?, ?, ?, ?)",
                            request.form.get("username"),
                            generate_password_hash(request.form.get("password")),
                            request.form.get("firstname"),
                            request.form.get("lastname"))
        except ValueError:
            return apology("username taken")

        # Log user in
        session["user_id"] = id

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")

    # GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Enable user to sell a stock."""

    # POST
    if request.method == "POST":
        
        # Record sale
        db.execute("""INSERT INTO items (user_id, type, event, date, time, location, price, payment, quantity, info, offers)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            session["user_id"], request.form.get("type"), request.form.get("event"), request.form.get("date"), request.form.get("time"), request.form.get("location"), request.form.get("price"), request.form.get("payment"), request.form.get("quantity"), request.form.get("info"), 0)

        # Insert item into transactions
        db.execute("""INSERT INTO transactions (user_id, type, transaction_type, event, date, price, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            session["user_id"], request.form.get("type"), "Sale", request.form.get("event"), request.form.get("date"), request.form.get("price"), request.form.get("quantity"))

        # Display profile
        flash("Posted!")
        return redirect("/")

    # GET
    else:
        # Display sales form
        return render_template("sell.html")

@app.route("/delete", methods=["POST"])
def delete():
    # POST
    id = request.form.get("id")
    # Delete item from transactions
    if id:
        db.execute("DELETE FROM transactions WHERE id = ?", id)
    return redirect("/profile")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
