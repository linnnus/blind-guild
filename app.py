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
CLIENT_SECRET = os.environ.get("CLIENT_ID") # DOTENV PAHAHAH
REDIRECT_URI = "https://localhost:8080/callback"
AUTH_BASE_URL = 'https://oauth.battle.net/authorize'
TOKEN_URL = "https://oauth.battle.net/token"
client = WebApplicationClient(CLIENT_ID)

app = Bottle()
plugin = sqlite.Plugin(dbfile="thisisadatabasethatcontainsdata.db")
app.install(plugin)

@app.route("/")
@app.route("/index.html")
def index():
    return template("index")

@app.route("/battle")
def battle():
    state = secrets.token_urlsafe(16)
    response.set_cookie('oauth_state', state)
    authorization_url = client.prepare_request_uri(AUTH_BASE_URL, redirect_uri=REDIRECT_URI, state=state)
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    state = request.get_cookie('oauth_state')
    code = request.query.get('code')
    oauth2_session = OAuth2Session(CLIENT_ID, state=state, redirect_uri=REDIRECT_URI)
    token_response = oauth2_session.fetch_token(TOKEN_URL, authorization_response=request.url, client_secret=CLIENT_SECRET)

    return f'Access token: {token_response.get("access_token")}'

@app.route("/join.html")
def join_form():
    return template("join")

@app.route("/join.html", method="POST")
def join_submission(db):
    name = request.forms.get("name")
    preferred_role = request.forms.get("preferredRole")
    motivation = request.forms.get("motivation")

    if name == None or name.strip() == "":
        raise HTTPError(400, "Namefield is empty or missing. ( warning: this is not good )")
    if preferred_role == None:
        raise HTTPError(400, "Preferred role is empty or missing.")
    if preferred_role not in ("dps", "tank", "healer"):
        raise HTTPError(400, "Preferred role must be one of the options (DPS, Tank, Healer) ( idiot )")
    if motivation == None or motivation.strip() == "":
        raise HTTPError(400, "Motivitaion field is empty or missing.")

    db.execute(f"INSERT INTO applications(name, role, motivation) VALUES ({name}, {preferred_role}, {motivation})")

@app.route("/<type:re:styles|images>/<filename>")
def server_static(type, filename):
    return static_file(filename, root=f"./static/{type}/")

debug(True)
run(app, host='localhost', port=8080, reloader=True,
    server="gevent", keyfile="./pki/server.key", certfile="./pki/server.crt")
