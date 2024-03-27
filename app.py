from bottle import Bottle, run, debug, static_file
from bottle import jinja2_template as template

app = Bottle()

@app.route("/")
def hello():
    return template("index")

@app.route("/static/<filename>")
def server_static(filename):
    return static_file(filename, root="./static/")

debug(True)
run(app, host='localhost', port=8080, reloader=True)