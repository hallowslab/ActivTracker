# ActivTracker

A simple, lightweight activity tracking web app built with `Flask` and `SQLAlchemy`.
It allows you to create actions (like “Run”, “Study”, “Workout”) and log entries with notes, and custom properties, it also adds an automatic timestamp.
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
- Python 3.13
- uv(optional, recommended)
- systemd
- nginx (optional, recommended)


### Clone the repository
```
git clone https://github.com/yourusername/ActivTracker.git
cd ActivTracker/src
```

### Create virtual environment & Install dependencies (UV example)
`uv sync`

### Initialize the database
`uv run python create_db.py`

### Configure .env
- Create a .env file inside the src directory by copying .env.template, then modify the following variables:
  - FLASK_ENV="development" - set to "production"
  - STATIC_ROOT=/var/www/activ/static - set to the root of where you will serve static assets with nginx

This will create a local SQLite database and initialize all tables.

### Generate a .secret
`uv run python generate_secret.py`

### Setup nginx
- Modify activitytracker.nginx to replace STATIC_ROOT with your actual path
- Copy the modified file to to `/etc/nginx/sites-available/activitytracker`
- Enable it with:
  `sudo ln -s /etc/nginx/sites-available/activitytracker /etc/nginx/sites-enabled/`
- Enable nginx with:
  `sudo nginx -t; sudo systemctl reload nginx`
- Create the STATIC_ROOT directory and add permissions:
  - `sudo mkdir -p STATIC_ROOT; sudo chmod -R 755 STATIC_ROOT; sudo chown -R USER:www-data STATIC_ROOT`
  - Remember to make sure to replace STATIC_ROOT and USER with their respective values, and www-data is the nginx group on debian derivatives
- Copy the static files to the STATIC_ROOT directory:
  - From the project's src directory run:
    `uv run flask collect-static`

### Setup systemd unit
- Modify activitytracker.service
  - replace USER with the user that will run the app
  - Change /home/USER/ActivTracker/src if you have the app outside the user's home directory (will need write perms)
  - Change STATIC_ROOT=/var/www/activ/static, if you changed in .env
- Copy the the modified file to /etc/systemd/system/activitytracker.service
- Enable the service:
  `sudo systemctl daemon-reload; sudo systemctl enable --now activitytracker`
- Check status with:
  `sudo systemctl status activitytracker`

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
