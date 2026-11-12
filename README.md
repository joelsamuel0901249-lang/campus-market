# Campus Market

A small, student focused freelance marketplace MVP. It uses only Python's standard library, SQLite, and browser native HTML/CSS/JavaScript.

## Run locally

Install Python 3.10 or newer, then from this folder run:

```sh
python server.py
```

Open <http://localhost:8000>. Set `PORT` to change the port or `CAMPUS_MARKET_DB` to store the SQLite database at another path. The database is created and seeded on first start. No real payments or campus verification are provided; profiles are student profiles only.

Explore using demo accounts (password for each: `demo1234`):

- maya.chen@campus.edu
- leo.martin@campus.edu
- amira.hassan@campus.edu
- noah.brooks@campus.edu
- sofia.park@campus.edu

New users can also sign up. To reset the demo data, stop the server and delete `campus_market.sqlite3` before starting again.

## Tests

```sh
python -m unittest discover -s tests -v
```

The API tests cover profile/listing ownership, proposals and poster-only freelancer selection, status permissions, reviews, input validation, and category filtering. There is no separate lint or build step because the app has no package dependencies or compilation step.
