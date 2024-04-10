from bottle import Bottle, run, debug, static_file, request, redirect, response
from bottle import jinja2_template as template
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
import secrets

CLIENT_ID = "x" # DOTENV ligger paa discorden, repoet er publkic saa det
CLIENT_SECRET = "x" # DOTENV PAHAHAH
REDIRECT_URI = "http://localhost:8080/callback"
# REDIRECT_URI = "https://google.com"

AUTH_BASE_URL = 'https://oauth.battle.net/authorize'
TOKEN_URL = "https://oauth.battle.net/token"
client = WebApplicationClient(CLIENT_ID)

app = Bottle()

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

@app.route("/<type:re:styles|images>/<filename>")
def server_static(type, filename):
    return static_file(filename, root=f"./static/{type}/")

debug(True)
run(app, host='localhost', port=8080, reloader=True)