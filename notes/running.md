# Running

This application is implemented as a WSGI python application.

## Running for development

For development purposes, we'll be running the application on localhost.

### Install dependencies

You'll probably want to start by setting up a virtual environment, though this
step is technically optional.

```
$ python3 -m pip install virtualenv
$ python3 -m virtualenv .venv
$ source .venv/bin/activate
```

All the applications dependencies are listed in the file `requirements.txt`. We
can instruct pythons package manager to read dependencies from that file.

```
$ python3 -m pip install -r requirements.txt
```

See [the note about manually patching dependencies](./patching-bottle_sqlite.md),
if you are running a version of Python greater than 3.9.

Note that on windows you may have to instead execute `py -m pip`. The procedure
for activating virtual environments will of course also differ slightly since
it's a different shell.

### Trust certificates

For development, we use our own CA. See [the note on installing certificates](./certificates.md).

### Run the server

To run the server just execute the following command from the projects root.

```
$ python3 app.py
```

For a live reloading version, `nodemon` can be used, if you have the node ecosystem installed.

```
$ npm i -g nodemon
$ nodemon --ext py,css,html,js --exec python3 app.py
```

## Running in production

TODO: Describe production setup.
