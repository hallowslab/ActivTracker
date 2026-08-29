# ActivTracker

A simple, lightweight activity tracking web app built with `Flask` and `SQLAlchemy`.
It allows you to create actions (like “Run”, “Study”, “Workout”),
  log entries with notes, and custom properties, it also adds an automatic timestamp.
You can then view trends and summaries through a visual dashboard.

---

## Features

- **User authentication** (register, login, logout, change password, delete account)
- **Action management**
  - Create, delete, view, and edit custom actions
  - Define per-action properties (stored as JSON)
- **Activity logs**
  - Add, delete, edit, and view logs for each action
  - Automatically timestamped
  - Optional notes and structured data
- **Visual summaries**
  - Chart.js dashboard
  - Interactive Period-based summaries (day/week/month)
  - Trend visualization over time
- **API & token-based access**
  - Secure API endpoints with expiring tokens
  - Designed for CLI or external integrations

---

## Tech Stack

| Component     |                Description                |
|---------------|-------------------------------------------|
| **Backend**   | Flask                                     |
| **Database**  | SQLite (via SQLAlchemy ORM)               |
| **Frontend**  | Jinja2 templates + Chart.js               |
| **Auth**      | Session-based (web) + Token-based (API)   |
| **Language**  | Python 3.13+                              |

---

## Native Setup

### Dependencies

- Python 3.13+
- uv
- make
- nginx
- openssl
- systemd

The nginx and systemd configs are generated from templates
(`deploy/templates/`) by a Makefile, which also generates the self-signed
SSL certificate, collects static assets, initializes the database, and
installs the service.

### Clone the repository

```sh
git clone https://github.com/hallowslab/ActivTracker.git
cd ActivTracker/src
```

### Create virtual environment & Install dependencies

```sh
uv sync
```

### Configure .env

Create a `.env` file inside the `src` directory by copying the template,
then adjust the values:

```sh
cp .env.template .env
```

- `FLASK_ENV` - set to `"production"` (never `development` in production)
- `USER` - the system user that will run the app; it must exist and own the
  project directory so it can write the SQLite database and `.secret`
- `STATIC_ROOT` - directory where static assets are served from by nginx
  (e.g. `/var/www/activ/static`)
- `DOMAIN` - the hostname nginx serves this app on (set this to your IP or
  add a hosts entry if you access the box by IP)
- `ENABLE_SSL` - `true` to generate a self-signed certificate and serve
  HTTPS (redirecting HTTP to HTTPS), `false` for plain HTTP
- `SSL_DIR` - directory the SSL certificate/key are installed to
  (only used when `ENABLE_SSL=true`)

The service template expects the app at `/home/<USER>/ActivTracker/src`.
If you clone it elsewhere (e.g. `/opt/ActivTracker`), edit
`deploy/templates/activitytracker.service.template` so `WorkingDirectory`
and `ExecStart` point at the real path.

### Deploy

```sh
make all
```

`make all` runs, in order:

1. `check` - verifies `openssl` and `nginx` are installed
2. `render` - fills in the nginx and systemd templates from `.env` and
   writes them to `deploy/rendered/`
3. `ssl` - generates a self-signed certificate (only when `ENABLE_SSL=true`)
   and installs it into `SSL_DIR`
4. `static` - creates `STATIC_ROOT` with correct ownership and copies the
   static files into it
5. `db` - creates the SQLite database and tables (`tracker.sqlite3`)
6. `secret` - generates `.secret` (required in production; the app refuses
   to start without it)
7. `nginx` - installs the rendered nginx config and reloads nginx
8. `systemd` - installs and starts the `activitytracker` service
   (gunicorn on port 8000)

Each step can also be run individually (e.g. `make static` after changing
`.env`), and `make clean` removes the service, nginx config, and generated
SSL certificates.

### Verify

```sh
sudo systemctl status activitytracker
sudo nginx -t
curl -k https://localhost/api/actions
```

A certificate warning on first visit is expected - it is self-signed.

---

## API Access

To use the REST API, generate a token first via the web UI, then send requests like:

- `curl -H "Authorization: Bearer YOUR_API_TOKEN" http://localhost:8000/api/actions`

Tokens automatically expire after their configured lifetime.

---

## Dashboard

### General summary

Visit `/dashboard/` to view graphical summaries of your actions and Charts with trends.

- Summary of all actions
- Trends of each individual action

### Activity summary

Visit `/dashboard/summary/activity` to view Charts of your actions and their trends.

- Select actions to visualize.
- Switch between day, week, and month views.
- See trendlines showing increases or decreases in actions over time.

---

## Testing

You can generate fake actions and logs to test summaries and graphs:

- `uv run flask create-test-data USERNAME NUM_ACTIONS DAYS`

This will populate your database with random actions data:
    - `USERNAME`: The user that will own the actions **THE USER MUST EXIST IN THE DATABASE**
    - `NUM_ACTIONS`: specify the number of actions to create
    - `DAYS` specifies how many days of activities to create.

---

## Future Ideas

- Support multiple users sharing dashboards
- Export action data (CSV/JSON)
- Add mobile-friendly responsive design(WIP)

---
