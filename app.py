from gevent import monkey; monkey.patch_all() # MUST BE FIRST IMPORT
from bottle import Bottle, run, debug, static_file, request, redirect, response, HTTPError
from bottle import jinja2_template as template
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import secrets
import os
import sqlite3
from bottle.ext import sqlite

load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID") # DOTENV ligger paa discorden, repoet er publkic saa det
CLIENT_SECRET = os.environ.get("CLIENT_SECRET") # DOTENV PAHAHAH
REDIRECT_URI = "https://localhost:8080/callback"
AUTH_BASE_URL = 'https://oauth.battle.net/authorize'
TOKEN_URL = "https://oauth.battle.net/token"
client = WebApplicationClient(CLIENT_ID)

DB_PATH = "thisisadatabasethatcontainsdata.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()
cursor.executescript("""
    CREATE TABLE IF NOT EXISTS applications (
        username VARCHAR(12) NOT NULL,
        preferredRole VARCHAR(6) NOT NULL,
        motivation TEXT NOT NULL,
        userId INTEGER NOT NULL
    );
""")
cursor.close()
connection.close()

app = Bottle()
plugin = sqlite.Plugin(dbfile=DB_PATH)
app.install(plugin)

@app.route("/")
@app.route("/index.html")
def index():
    return template("index")

@app.route("/join_intro.html")
def join_intro():
    return template("join_intro")

@app.route("/battle")
def battle():
    state = secrets.token_urlsafe(16)
    response.set_cookie('oauth_state', state)
    authorization_url = client.prepare_request_uri(AUTH_BASE_URL, redirect_uri=REDIRECT_URI, state=state)
    return redirect(authorization_url)

@app.route('/callback')
def join_form():
    state = request.get_cookie('oauth_state')
    oauth2_session = OAuth2Session(CLIENT_ID, state=state, redirect_uri=REDIRECT_URI)
    token_response = oauth2_session.fetch_token(TOKEN_URL, authorization_response=request.url, client_secret=CLIENT_SECRET)

    # Get the user ID of the just authenticated user. As per the API
    # documentation, this should be used to identify users.
    #
    # See: https://develop.battle.net/documentation/guides/regionality-and-apis#:~:text=Developers%20should%20use%20an%20accountId
    query_parameters = {
            "region": "eu",
    }
    response = oauth2_session.get("https://oauth.battle.net/oauth/userinfo", params=query_parameters)
    response.raise_for_status()
    user_info = response.json()
    user_id = user_info["id"]

    # We pass the token retrieved here so it can be submitted with the rest of the application.
    return template("join_form", user_id=user_id)

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

    # FIXME: The user id is a 64-bit unsigned integer which may be larger than the INTEGER type of sqlite3.
    db.execute(f"INSERT INTO applications(username, preferredRole, motivation, userId) VALUES (?, ?, ?, ?)", (name, preferred_role, motivation, user_id))

    return template("join_success")

@app.route("/<type:re:styles|images>/<filename>")
def server_static(type, filename):
    return static_file(filename, root=f"./static/{type}/")

debug(True)
run(app, host='localhost', port=8080, reloader=True,
    server="gevent", keyfile="./pki/server.key", certfile="./pki/server.crt")
