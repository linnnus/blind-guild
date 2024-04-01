from bottle import Bottle, run, debug, static_file
from bottle import jinja2_template as template

app = Bottle()

@app.route("/")
@app.route("/index.html")
def index():
    return template("index")

@app.route("/join.html")
def join_form():
    return template("join")

@app.route("/<type:re:styles|images>/<filename>")
def server_static(type, filename):
    return static_file(filename, root=f"./static/{type}/")

debug(True)
run(app, host='localhost', port=8080, reloader=True)