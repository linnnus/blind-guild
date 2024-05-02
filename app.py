from gevent import monkey; monkey.patch_all() # MUST BE FIRST IMPORT
from bottle import Bottle, run, debug, static_file, request, redirect, response, HTTPError
from bottle import jinja2_template
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import secrets
import os
import sqlite3
from bottle.ext import sqlite
from beaker.middleware import SessionMiddleware
import functools
import datetime

load_dotenv()

REGION = "eu"

# OAuth2 variable declarations
CLIENT_ID = os.environ.get("CLIENT_ID") # DOTENV ligger paa discorden, repoet er publkic saa det
CLIENT_SECRET = os.environ.get("CLIENT_SECRET") # DOTENV PAHAHAH
LOGIN_REDIRECT_URI = "https://localhost:8080/login_callback"
JOIN_REDIRECT_URI = "https://localhost:8080/join_callback"
AUTH_BASE_URL = 'https://oauth.battle.net/authorize'
TOKEN_URL = "https://oauth.battle.net/token"
SCOPE = "wow.profile"
client = WebApplicationClient(CLIENT_ID)

# Database initialization
DB_PATH = "thisisadatabasethatcontainsdata.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()
cursor.executescript("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY,
        username VARCHAR(12) NOT NULL,
        userId INTEGER UNIQUE NOT NULL,
        preferredRole VARCHAR(6) NOT NULL,
        motivation TEXT NOT NULL,
        applicationTime INT NOT NULL          -- unix timestamp
    );
    INSERT OR IGNORE
    INTO applications(username, userId, preferredRole, motivation, applicationTime)
    VALUES
        ('DillerBlaster69', 0, 'dps',    'fake motivation',    strftime('%s','now')),
        ('DillerDiller',    1, 'healer', 'fake motivation',    strftime('%s','now')),
        ('diller123',       2, 'tank',   'fake motivation',    strftime('%s','now')),
        ('susamongus',      3, 'dps',    'fake motivation #4', strftime('%s','now'));

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(12) NOT NULL,
        userId INTEGER UNIQUE NOT NULL,
        preferredRole VARCHAR(6) NOT NULL,
        joinTime INT NOT NULL                 -- unix timestamp
    );
    INSERT OR IGNORE INTO users(username, userId, preferredRole, joinTime) VALUES ('linuspwn', 1165955606, 'dps', strftime('%s','now'));
""")
cursor.close()
connection.close()

app = Bottle()
app.install(sqlite.Plugin(dbfile=DB_PATH))
app_wrapped = SessionMiddleware(app, config={
    "session.type": "file",
    "session.cookie_expires": 300,
    "session.data_dir": "./sessions",
    "session.auto": True,
})

def template(*args, **kwargs):
    session = request.environ.get("beaker.session")
    assert session is not None
    logged_in = session.has_key("user_id")
    return jinja2_template(*args, **kwargs, logged_in=logged_in)

@app.route("/")
@app.route("/index.html")
def index():
    return template("index")

@app.route("/leaderboards.html")
def leaderboards(db: sqlite3.Connection):
    def human_time_since(timestamp: int):
        dt = datetime.datetime.fromtimestamp(timestamp)
        delta: datetime.timedelta = datetime.datetime.now() - dt

        seconds = int(delta.total_seconds())
        periods = [
            ('year',        60*60*24*365),
            ('month',       60*60*24*30),
            ('day',         60*60*24),
            ('hour',        60*60),
            ('minute',      60),
        ]

        strings=[]
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value , seconds = divmod(seconds, period_seconds)
                has_s = 's' if period_value > 1 else ''
                strings.append("%s %s%s" % (period_value, period_name, has_s))

        if strings:
            return ", ".join(strings)
        else:
            has_s = 's' if seconds > 1 else ''
            return f"{seconds} second{has_s}"

    all_members = db.execute("SELECT username, joinTime FROM users ORDER BY joinTime");
    return template("leaderboards.html", all_members=all_members, human_time_since=human_time_since)

@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    response.set_cookie('oauth_state', state)
    authorization_url = client.prepare_request_uri(AUTH_BASE_URL, redirect_uri=LOGIN_REDIRECT_URI, state=state, scope=SCOPE, wad="foo")
    return redirect(authorization_url)

@app.route("/login_callback")
def login_callback(db: sqlite3.Connection):
    # Get user ID associated with auth token
    state = request.get_cookie('oauth_state')
    oauth2_session = OAuth2Session(client_id=CLIENT_ID, state=state, redirect_uri=LOGIN_REDIRECT_URI)
    oauth2_session.fetch_token(TOKEN_URL, authorization_response=request.url, client_secret=CLIENT_SECRET)
    query_parameters = { "region": REGION }
    response = oauth2_session.get("https://oauth.battle.net/oauth/userinfo", params=query_parameters)
    response.raise_for_status()
    user_info = response.json()
    user_id = user_info["id"]

    # Ensure user in database
    row = db.execute("SELECT * FROM users WHERE userId = ?", [user_id]).fetchone()
    if row == None:
        raise HTTPError(404, f"User with id {user_id} not found")

    # Store session for subsequent requests
    session = request.environ.get("beaker.session")
    session["user_id"] = user_id
    session.save()

    return redirect("/index.html")

@app.route("/join_intro.html")
def join_intro():
    return template("join_intro")

@app.route("/battle")
def battle():
    state = secrets.token_urlsafe(16)
    response.set_cookie('oauth_state', state)
    authorization_url = client.prepare_request_uri(AUTH_BASE_URL, redirect_uri=JOIN_REDIRECT_URI, state=state, scope=SCOPE)
    return redirect(authorization_url)

@app.route('/callback')
@app.route('/join_callback')
def join_form():
    state = request.get_cookie('oauth_state')
    oauth2_session = OAuth2Session(CLIENT_ID, state=state, redirect_uri=JOIN_REDIRECT_URI)
    oauth2_session.fetch_token(TOKEN_URL, authorization_response=request.url, client_secret=CLIENT_SECRET)

    # Get the user ID of the just authenticated user. As per the API
    # documentation, this should be used to identify users.
    #
    # See: https://develop.battle.net/documentation/guides/regionality-and-apis#:~:text=Developers%20should%20use%20an%20accountId
    query_parameters = {
            "region": REGION,
    }
    response = oauth2_session.get("https://oauth.battle.net/oauth/userinfo", params=query_parameters)
    response.raise_for_status()
    user_info = response.json()
    user_id = user_info["id"]

    # do we have it? yes
    query_parameters = {
        "region": REGION,
        "namespace": f"profile-{REGION}",
        "locale": "en_US",
    }
    response = oauth2_session.get(f"https://{REGION}.api.blizzard.com/profile/user/wow", params=query_parameters)
    response.raise_for_status()
    data = response.json()
    print(response.text)
    characters = []
    for account in data["wow_accounts"]:
        for character in account["characters"]:
            characters.append(character)

    # We pass the token retrieved here so it can be submitted with the rest of the application.
    return template("join_form", user_id=user_id, characters=characters)

@app.route("/callback", method="POST")
def join_submission(db: sqlite3.Connection):
    name = request.forms.get("name")
    preferred_role = request.forms.get("preferredRole")
    motivation = request.forms.get("motivation")
    user_id = request.forms.get("userId")

    if name == None or name.strip() == "":
        raise HTTPError(400, "Namefield is empty or missing. ( warning: this is not good )")
    if preferred_role == None:
        raise HTTPError(400, "Preferred role is empty or missing.")
    if preferred_role not in ("dps", "tank", "healer"):
        raise HTTPError(400, "Preferred role must be one of the options (DPS, Tank, Healer) ( idiot )")
    if motivation == None or motivation.strip() == "":
        raise HTTPError(400, "Motivitaion field is empty or missing.")
    if user_id == None or not user_id.isdigit():
        raise HTTPError(400, "Missing or invalid user id")

    try:
        db.execute("""
            INSERT
            INTO applications(username, userId, preferredRole, motivation, applicationTime)
            VALUES (?, ?, ?, strftime('%s','now'), ?)
        """, (name, user_id, preferred_role, motivation))
    except sqlite3.IntegrityError as e:
        print(e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE)
        print(str(e))
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            # The database (model) rejected the application because the unique constraint wasn't met!
            raise HTTPError(400, "You've already submitted an application!")
        else:
            raise

    return template("join_success")

def require_authentication(fn):
    """Decorator that ensures the client is logged in"""
    @functools.wraps(fn)
    def wrapped(db: sqlite3.Connection, *args, **kwargs):
        # Ensure authentication
        session = request.environ.get("beaker.session")
        print(session)
        user_id = session.get("user_id", None)
        if user_id is None:
            raise HTTPError(403, "Must be logged in! (missing cookie)")
        user = db.execute("SELECT * FROM users WHERE userId = ?", [user_id]).fetchone()
        if user is None:
            raise HTTPError(403, "Must be logged in! (unknown user)")

        # Wrapped function may or may not want this
        kwargs["db"] = db

        return fn(*args, **kwargs)
    return wrapped

@require_authentication
@app.route("/manage.html")
def manage(db: sqlite3.Connection):
    applications = db.execute("SELECT * FROM applications").fetchall();
    return template("manage", applications=applications)


@require_authentication
@app.route("/manage/<action:re:accept|reject>/<user_id:int>", method="POST")
def approve_application(action: str, user_id: int, db: sqlite3.Connection):
    if action == "accept":
        db.execute("""
            INSERT INTO users(username, userId, preferredRole, joinTime)
            SELECT username, userId, preferredRole, strftime('%s','now')
            FROM applications
            WHERE userId = ?;
       """, [user_id])
    print(user_id)
    db.execute("DELETE FROM applications WHERE userId = ?", [user_id])

    return f"Application {action}ed!"

@app.route("/<type:re:styles|images>/<filename>")
def server_static(type, filename):
    return static_file(filename, root=f"./static/{type}/")

debug(True)
run(app_wrapped, host='localhost', port=8080, server="gevent", keyfile="./pki/server.key", certfile="./pki/server.crt", reloader=True)
