# Bottle sqlite sucks ass
It's outdated as fuck. In line 114 of "bottle_sqlite.py" a deprecated function is being used (this shit isnt updated)
getargspec() is deprecated, swap with getfullargspec() and it works
