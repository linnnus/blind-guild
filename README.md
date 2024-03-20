# Blind Guild site (?)

This repository contains a web server which implements some guild management stuff, I guess.

## Project layout

The main server is implemented in `app.py`.

`views/` contains Jinja2 templates.
These are rendered using the `template()` function.

`static/` is for files that never change.
All HTTP requests that begin with `/static/` will be resolved relative to this file.
