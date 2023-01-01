import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    portfolio_data = db.execute("SELECT userID, stockSymbol, SUM(stockAmount) FROM portfolio WHERE userID=? GROUP BY stockSymbol", session["user_id"])

    stock_value = 0
    for stock_data in portfolio_data:
        stock = dict(lookup(stock_data['stockSymbol']))
        db.execute("UPDATE portfolio SET stockValue=? WHERE stockSymbol= ?", stock['price'], stock['symbol'])
        db.execute("UPDATE portfolio SET stockName=? WHERE stockSymbol= ?", stock['name'], stock['symbol'])
        stock_value += (stock_data['SUM(stockAmount)'] * stock['price'])

    user_data = db.execute("SELECT * FROM users WHERE id= ?", session["user_id"])
    cash_amount = user_data[0]['cash']

    portfolio_updated = db.execute("SELECT * FROM portfolio WHERE userID= ? GROUP BY stockSymbol", session["user_id"])
    return render_template("index.html", portfolio_updated=portfolio_updated, cash_amount=cash_amount, stock_value=stock_value)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        stock_symbol = request.form.get("symbol")
        buy_amount = request.form.get("shares")

        if not stock_symbol or not buy_amount:
            return apology("You submited blank input")
        if not buy_amount.isdigit():
            return apology("Amount must be positive")
        if lookup(stock_symbol) == None:
            return apology("This stock doesn't exist")
        if int(buy_amount) < 1:
            return apology("Make sure you insert correct amount")
        quoted_stock = dict(lookup(stock_symbol))
        user_data = db.execute("SELECT * FROM users WHERE id= ?", session["user_id"])
        if (int(buy_amount) * quoted_stock['price']) > user_data[0]["cash"]:
            return apology("You don't have enough cash.")

        transaction_value = int(buy_amount) * quoted_stock['price']
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cash_after = user_data[0]["cash"] - transaction_value
        db.execute("UPDATE users SET cash= ? WHERE id=?", cash_after, session['user_id'])
        portfolio_data = db.execute("SELECT * FROM portfolio WHERE (userID=? and stockSymbol=?)",
                                    session['user_id'], stock_symbol.upper())
        if len(portfolio_data) == 0:
            db.execute("INSERT INTO portfolio (userID, stockSymbol, stockAmount) VALUES (?, ?, ?)",
                    session['user_id'], stock_symbol.upper(), int(buy_amount))
        else:
            amount_after = portfolio_data[0]["stockAmount"] + int(buy_amount)
            db.execute("UPDATE portfolio SET stockAmount= ? WHERE (userID=? and stockSymbol=?)",
                    int(amount_after), session['user_id'], stock_symbol)

        db.execute("INSERT INTO transactionHistory (userID, stockName, stockAmount, transactionType, transactionDate, cash) VALUES (?, ?, ?, 1, ?, ?)",
                session["user_id"], stock_symbol, int(buy_amount), time_now, transaction_value)
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history_data = db.execute("SELECT * FROM transactionHistory WHERE userID=? ORDER BY transactionDate DESC", session['user_id'])
    return render_template("history.html", history_data=history_data)


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
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol_search = request.form.get("symbol")

        if not symbol_search:
            return apology("You submited blank input")
        if lookup(symbol_search) == None:
            return apology("This stock doesn't exist")

        quoted_stock = dict(lookup(symbol_search))
        stock_symbol = quoted_stock['symbol']
        stock_name = quoted_stock['name']
        stock_price = quoted_stock['price']

        return render_template("quoted.html", stock_symbol=stock_symbol, stock_name=stock_name, stock_price=stock_price)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method=="POST":
        username_sql = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if not request.form.get("username"):
            return apology("must provide username")
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("password must be the same")

        elif len(username_sql) == 1:
            return apology("username is already taken")

        password = request.form.get("password")
        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash, cash) VALUES (?, ?, 10000)", request.form.get("username"), hashed_password)

        sql_data = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = sql_data[0]["id"]

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method=="POST":
        stock_symbol = request.form.get("symbol")
        sell_amount = request.form.get("shares")

        if not stock_symbol or not sell_amount:
            return apology("You submited blank input")
        if lookup(stock_symbol) == None:
            return apology("This stock doesn't exist")
        if int(sell_amount) < 1:
            return apology("Make sure you insert correct amount")

        user_portfolio = db.execute("SELECT * FROM portfolio WHERE (userID= ? AND stockSymbol= ?)",
                                    session['user_id'], stock_symbol)
        if int(sell_amount) > user_portfolio[0]["stockAmount"]:
            return apology("You don't have that amount of this stock.")

        stock = dict(lookup(stock_symbol))
        user_data = db.execute("SELECT * FROM users WHERE id= ?", session["user_id"])
        amount_after = user_portfolio[0]["stockAmount"] - int(sell_amount)
        transaction_value = stock['price'] * int(sell_amount)
        cash_after = user_data[0]["cash"] + transaction_value
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if amount_after == 0:
            db.execute("DELETE FROM portfolio WHERE (userID=? and stockSymbol=?)",session['user_id'], stock_symbol)
        else:
            db.execute("UPDATE portfolio SET stockAmount= ? WHERE (userID=? and stockSymbol=?)",
                    int(amount_after), session['user_id'], stock_symbol)

        db.execute("UPDATE users SET cash= ? WHERE id=?", cash_after, session['user_id'])
        db.execute("INSERT INTO transactionHistory (userID, stockName, stockAmount, transactionType, transactionDate, cash) VALUES (?, ?, ?, 0, ?, ?)",
                session['user_id'], stock_symbol, int(sell_amount), time_now, transaction_value)

        return redirect("/")
    else:
        stock_name = db.execute("SELECT stockSymbol FROM portfolio WHERE userID= ?", session['user_id'])
        return render_template("sell.html", stock_name=stock_name)


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    """Show history of transactions"""
    if request.method == "POST":
        money_deposit = request.form.get("deposit_amount")
        user_cash = db.execute("SELECT * FROM users WHERE id= ?", session['user_id'])
        cash_after = float(money_deposit) + user_cash[0]['cash']
        db.execute("UPDATE users SET cash= ? WHERE id= ?", cash_after, session['user_id'])
        return redirect("/")
    else:
        return render_template("deposit.html")