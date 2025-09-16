"""
x.py
------
Purpose:
- Connect to the MySQL database (db function)
- Validate user input (names, email, password)
- Provide a no_cache decorator to prevent showing cached pages after logout

Notes:
- Only some validators are used right now (name, email, password).
- Others (confirm password, UUID) are examples for later use.
"""
from flask import request, make_response
import mysql.connector
import re
from functools import wraps           

from icecream import ic
ic.configureOutput(prefix=f'----- | ', includeContext=True)

UPLOAD_ITEM_FOLDER = './images'

############################## DATABASE CONNECTION ##############################
"""
 Create a connection to the database.
    - mysql.connector.connect(...) opens the connection
    - host: where the database server is running (here "mariadb" = Docker service name)
    - user: MySQL username
    - password: MySQL password
    - database: which database/schema to use (here "twitter")

    cursor(dictionary=True) means:
    - Results will come back as Python dictionaries, not just tuples.
    - Example: row["user_name"] instead of row[0]

    Returns:
      db     -> the connection (so we can commit/rollback/close)
      cursor -> the cursor to run SQL queries

    If connection fails:
      - Print the error to the terminal
      - Raise a new Exception with a custom message that app.py can catch
    """
def db():
    try:
        db = mysql.connector.connect(
            host="mariadb",
            user="root",
            password="password",
            database="twitter"
        )
        cursor = db.cursor(dictionary=True)
        return db, cursor
    except Exception as e:
        print(e, flush=True)
        raise Exception("Twitter exception - Database under maintenance", 500)
############################## VALIDATION: USERNAME / FIRST NAME / LAST NAME ##############################
# ---------- USER NAME ----------
USER_NAME_MIN = 2
USER_NAME_MAX = 20
def validate_user_name(user_name: str):
    if len(user_name) < USER_NAME_MIN:
        raise Exception("twitter exception - user name too short")
    if len(user_name) > USER_NAME_MAX:
        raise Exception("twitter exception - user name too long")
    return user_name.strip()

# ---------- FIRST NAME ----------
USER_FIRST_NAME_MIN = 2
USER_FIRST_NAME_MAX = 20
def validate_user_first_name(user_first_name: str):
    if len(user_first_name) < USER_FIRST_NAME_MIN:
        raise Exception("twitter exception - user first name too short")
    if len(user_first_name) > USER_FIRST_NAME_MAX:
        raise Exception("twitter exception - user first name too long")
    return user_first_name.strip()

# ---------- LAST NAME ----------
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
def validate_user_last_name(user_last_name: str):
    if len(user_last_name) < USER_LAST_NAME_MIN:
        raise Exception("twitter exception - user last name too short")
    if len(user_last_name) > USER_LAST_NAME_MAX:
        raise Exception("twitter exception - user last name too long")
    return user_last_name.strip()

############################## NO CACHE DECORATOR ##############################
""" Decorator that disables browser caching.
- Prevents showing protected pages with Back button after logout.
- Adds HTTP headers to force reload from server.
 Purpose:
 - After logout, the user should NOT be able to press the back button
 Usage:
 @x.no_cache
 def view_home(): ...
"""
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        # these headers tell the browser not to cache the page
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache_view

############################## VALIDATION: EMAIL ##############################
"""
    Validate user_email from the form.
    - Get the value from request.form (default empty string if missing)
    - Remove spaces
    - Match against REGEX_EMAIL
    - If invalid, raise an Exception (so app.py can return "invalid email")
"""
REGEX_EMAIL = r"^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
def validate_user_email():
    user_email = request.form.get("user_email", "").strip()
    if not re.match(REGEX_EMAIL, user_email):
        raise Exception("Twitter exception - Invalid email", 400)
    return user_email


############################### VALIDATION: PASSWORD ##############################
"""
    Validate password from the form.
    - Must be 4–50 characters (for easy testing now, can be increased later)
    - Uses regex to check the length
    - If invalid, raise Exception
"""
USER_PASSWORD_MIN = 4
USER_PASSWORD_MAX = 50
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$"
def validate_user_password():
    user_password = request.form.get("user_password", "").strip()
    if not re.match(REGEX_USER_PASSWORD, user_password):
        raise Exception("Twitter exception - Invalid password", 400)
    return user_password

############################## VALIDATION: PASSWORD CONFIRM ##############################
"""
If the form asks the user to type the password twice,
this function validates the second field (confirm). I don't have it thooo
"""
def validate_user_password_confirm():
    user_password = request.form.get("user_password_confirm", "").strip()
    if not re.match(REGEX_USER_PASSWORD, user_password):
        raise Exception("Twitter exception - Invalid confirm password", 400)
    return user_password

############################## VALIDATION: UUID4 ##############################
"""
Validate that the string is a valid UUID v4.
If no uuid4 is passed as an argument, it will try
to read it from request.values. I don't use this one either
"""
REGEX_UUID4 = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
def validate_uuid4(uuid4 = ""):
    if not uuid4:
        uuid4 = request.values.get("uuid4", "").strip()
    if not re.match(REGEX_UUID4, uuid4):
        raise Exception("Twitter exception - Invalid uuid4", 400)
    return uuid4