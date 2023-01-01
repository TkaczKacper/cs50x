import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///birthdays.db")
months31day = [1, 3, 5, 7, 8, 10, 12]
months30day = [4, 6, 9, 11]

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        month = request.form.get("month")
        day = request.form.get("day")
        if not name or not month or not day:
            return render_template("failure.html", message="Some field are missing!")
        if int(month) > 12:
            return render_template("failure.html", message="Hey, year has only 12 months!")
        if (int(day) > 29 and int(month) == 2 or (int(day) > 30 and (int(month) in months30day)) or (int(day) > 31 and (int(month) in months31day))):
            return render_template("failure.html", message="Hey, this month can't have so many days!")
        else:
            db.execute("INSERT INTO birthdays (name, month, day) VALUES (?, ?, ?)", name, month, day)
            return redirect("/")

    else:
        birthdays = db.execute("SELECT * FROM birthdays")
        return render_template("index.html", birthdays=birthdays)


