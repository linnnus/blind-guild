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
        username VARCHAR(12) NOT NULL,
        preferredRole VARCHAR(6) NOT NULL,
        motivation TEXT NOT NULL,
        userId INTEGER UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        userId INTEGER UNIQUE NOT NULL,
        role VARCHAR(6) NOT NULL
    );
    INSERT OR IGNORE INTO users(userId, role) VALUES (1165955606, 'dps');
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
        raise HTTPError(404, "User not found")

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
        db.execute("INSERT INTO applications(username, preferredRole, motivation, userId) VALUES (?, ?, ?, ?)", (name, preferred_role, motivation, user_id))
    except sqlite3.IntegrityError as e:
        print(e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE)
        print(str(e))
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            # The database (model) rejected the application because the unique constraint wasn't met!
            raise HTTPError(400, "You've already submitted an application!")
        else:
            raise

    return template("join_success")

@app.route("/<type:re:styles|images>/<filename>")
def server_static(type, filename):
    return static_file(filename, root=f"./static/{type}/")

debug(True)
run(app_wrapped, host='localhost', port=8080, server="gevent", keyfile="./pki/server.key", certfile="./pki/server.crt", reloader=True)
