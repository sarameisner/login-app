"""
app.py
------
Purpose:
- Define all the routes (signup, login, home, logout)
- Handle the request/response flow
- Use validators from x.py to check user input
- Hash passwords on signup, check them on login
- Use sessions to remember who is logged in
- Apply @x.no_cache to prevent showing cached pages after logout

Flow:
1) User signs up -> we validate input, hash password and save in DB
2) User logs in -> we fetch by email, check password hash, start session
3) User visits /home -> only allowed if session exists
4) User logs out -> session is cleared -> cannot go back with browser back button
"""
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import x 
from icecream import ic
import time
import uuid
import os

ic.configureOutput(prefix=f'----- | ', includeContext=True)

app = Flask(__name__)

# Max upload størrelse
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024   # 1 MB

# Sessions
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


##############################
##############################
##############################
def _____USER_____(): pass 
##############################
##############################
##############################


@app.get("/")
def view_index():
    return render_template("index.html")


# ---------- SIGNUP ----------
@app.get("/signup")
def view_signup():
    return render_template("signup.html")


@app.post("/signup")
def handle_signup():
    # sign up flow
    # 1) read and validate the name etc
    # 2) hash the password
    # 3) INSERT user in DB inside a transaction
    # 4) commit on succes, rollback on error
    # 5) return clear messages + proper http status codes
    try:
        # 1) read and validate
        user_name = request.form.get("user_name", "").strip()
        x.validate_user_name(user_name)

        user_first_name = request.form.get("user_first_name", "").strip()
        x.validate_user_first_name(user_first_name)

        user_last_name = request.form.get("user_last_name", "").strip()
        x.validate_user_last_name(user_last_name)

        # validate email and password via x
        user_email = x.validate_user_email()
        user_password = x.validate_user_password()
        # 2) hash the password
        user_password_hash = generate_password_hash(user_password)
        # 3) open the db connection and start a transaction
        db, cursor = x.db()
        db.start_transaction()

        # Indsætter i kolonnerne inkl. user_password_hash
        q = """
        INSERT INTO users
          (user_name, user_first_name, user_last_name, user_email, user_password_hash)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(q, (user_name, user_first_name, user_last_name, user_email, user_password_hash))
        inserted_rows = cursor.rowcount
        # 4) commit the transaction 
        db.commit()
        # return a succes message
        return f"total rows inserted: {inserted_rows}", 200

    except Exception as ex:
        # any error: log ir, rollback and map to a clear response
        ic(ex)
        if "db" in locals(): db.rollback()
        # validation messages mapped from x.py exceptions
        if "twitter exception - user name too short" in str(ex):  return "name too short", 400
        if "twitter exception - user name too long"  in str(ex):  return "name too long", 400
        if "twitter exception - user first name too short" in str(ex): return "first name too short", 400
        if "twitter exception - user first name too long"  in str(ex): return "first name too long", 400
        if "twitter exception - user last name too short"  in str(ex): return "last name too short", 400
        if "twitter exception - user last name too long"   in str(ex): return "last name too long", 400
        if "Twitter exception - Invalid email" in str(ex):        return "invalid email", 400
        if "Twitter exception - Invalid password" in str(ex):     return "invalid password", 400

        if "Duplicate entry" in str(ex):
            if "user_email" in str(ex): return "email already in use", 409
            if "user_name"  in str(ex): return "username already in use", 409
            return "email or username already in use", 409

        return "system under maintenance", 500
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


# ---------- LOGIN view ----------
@app.get("/login")
def view_login():
    return render_template("login.html")

# ---------- LOGIN handler ----------
@app.post("/login")
def handle_login():
    # login flow
    # 1) validate email/password format
    # 2) SELECT user by email 
    # 3) compare password using check_password:hash
    # 4) create a session and redirect to /home
    try:
        # 1) validate
        user_email = x.validate_user_email()
        user_password = x.validate_user_password()
        # 2) fetch user by email
        db, cursor = x.db()
        q = "SELECT * FROM users WHERE user_email = %s LIMIT 1"
        cursor.execute(q, (user_email,))
        user = cursor.fetchone()
        # if no user or password mismatch
        if not user:
            return "invalid credentials", 400
        # uses the hashed password stored in user_password_hash
        if not check_password_hash(user["user_password_hash"], user_password):
            return "invalid credentials", 400
        # create a clean session
        session.clear()
        session["user_pk"] = user["user_pk"]
        session["user_first_name"] = user["user_first_name"]
        session["user_name"] = user["user_name"]
        # redirect to the protected page
        return redirect(url_for("view_home")), 302

    except Exception as ex:
        ic(ex)
        # map validator errors to 400 Bad Request
        if "Invalid email" in str(ex):    return "invalid email", 400
        if "Invalid password" in str(ex): return "invalid password", 400
        # anything else - 500 Internal Server Error
        return "system under maintenance", 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


# ---------- HOME (protected) ----------
@app.get("/home")
# prevents showing cached content after logout / back button
@x.no_cache
def view_home():
    if "user_pk" not in session:
        return redirect(url_for("view_login"))
    return render_template("home.html", first_name=session.get("user_first_name", "User"))


# ---------- LOGOUT ----------
@app.post("/logout")
# also set no-cache on logout responses
@x.no_cache 
def handle_logout():
    # clear the session so the user is logged out
    session.clear()
    return redirect(url_for("view_login"))