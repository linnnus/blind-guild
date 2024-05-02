# Patching `bottle_sqlite`

This library is a little outdated, so if you're running a version of Python
newer than 3.9, you will need to manually patch it before running.

In line 114 of `bottle_sqlite.py` a deprecated function is being used.
`getargspec()` is deprecated, swap with `getfullargspec()` and the library
should continue working.
