# ActivTracker

A simple, lightweight activity tracking web app built with <code>Flask</code> and <code>SQLAlchemy</code>.
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


### 1. Clone the repository
<code>
git clone https://github.com/yourusername/ActivTracker.git
cd ActivTracker
</code>

### 2. Create virtual environment & Install dependencies (UV example)
<code>
uv sync
</code>

### 3. Initialize the database
<code>
uv run python create_db.py
</code>

### 4. Configure .env
- Create a file named .env inside src from the template .env.template and modify the variables
  - FLASK_ENV="development" - set to "production"
  - STATIC_ROOT=/var/www/activ/static - set to the root of where you will serve static assets with nginx

This will create a local SQLite database and initialize all tables.

### 4. Setup nginx
- Modify activitytracker.nginx replace STATIC_ROOT
- Copy the modified file to to /etc/nginx/sites-available/activitytracker
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

<code>
curl -H "Authorization: Bearer YOUR_API_TOKEN" http://localhost:5000/api/actions
</code>

Tokens automatically expire after their configured lifetime.

---

## Dashboard

Visit <code>/dashboard/summary</code> to view graphical summaries of your activity trends.
- Select actions to visualize.
- Switch between day, week, and month views.
- See trendlines showing increases or decreases in activity over time.

---

## Command Line Tools

A small management script (<code>generate_secret.py</code>) is included to generate a <code>.secret</code> file containing a secure key:

<code>
uv run python generate_secret.py
</code>

---

## Testing

You can generate fake actions and logs to test summaries and graphs:

<code>
uv run flask create-test-data USERNAME NUM_ACTIONS DAYS
</code>

This will populate your database with random activity data:
    - `USERNAME`: The user that will own the tasks **THE USER MUST EXIST IN THE DATABASE**
    - `NUM_ACTIONS`: specify the number of actions to create
    - `DAYS` specifies how many days of activities to create.

---

## Future Ideas

- Support multiple users sharing dashboards
- Export activity data (CSV/JSON)
- Add mobile-friendly responsive design(WIP)

---
