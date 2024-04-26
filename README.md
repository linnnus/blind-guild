# Blind Guild site (?)

This repository contains a web server which implements some guild management stuff, I guess.

## Project layout

The main server is implemented in `app.py`.

`views/` contains Jinja2 templates.
These are rendered using the `bottle#template_jinja()` function,
imported as `template()` in `app.py`.
Every view `views/X.html` has a corresponding `static/styles/X.css`
containing styles specific to that view.
Global styles are thus contained in `static/styles/base.css`
since that template forms the base for all other views.

`pki/` contains a certificate chain necessary for HTTPS support during development.
See [`notes/certificates.md`](./notes/certificates.md) for more information.

`static/` is for files that never change.
All HTTP requests that begin with `/images/` or `/styles/` will be resolved relative to their corresponding subfolder in `static/`.
