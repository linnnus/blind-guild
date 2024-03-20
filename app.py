from bottle import Bottle, run
from bottle import jinja2_template as template

app = Bottle()

@app.route("/")
def hello():
    return template("index")

run(app, host='localhost', port=8080)
