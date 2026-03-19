# 📋 Job Application Tracker API

A production-ready REST API for tracking job applications, interview stages, and follow-up reminders — built with **FastAPI**, **MySQL**, and **Docker**.



\---

## 🚀 Features

* 🔐 **JWT Authentication** — Secure register/login with hashed passwords
* 📄 **Full CRUD** — Manage job applications and nested interview records
* 📊 **Stats Dashboard** — Get counts by application status at a glance
* 🔍 **Filter \& Search** — Filter by status, search by company name, with pagination
* 📧 **Email Reminders** — Automated follow-up and interview reminder emails via SMTP
* ⏰ **Background Scheduler** — APScheduler runs reminder checks every few hours
* 🐳 **Docker + Docker Compose** — One-command setup with MySQL
* 📖 **Auto Swagger Docs** — Interactive API docs at `/docs`
* 🧪 **Unit Tests** — Full test coverage using `pytest` and SQLite in-memory DB
* 🌐 **Basic Frontend** — HTML/CSS/JS dashboard served from the API

\---

## 🛠️ Tech Stack

|Layer|Technology|
|-|-|
|Framework|FastAPI|
|Database|MySQL 8 + SQLAlchemy ORM|
|Auth|JWT (python-jose) + bcrypt|
|Email|FastAPI-Mail (SMTP)|
|Scheduler|APScheduler|
|Migrations|Alembic|
|Testing|Pytest + HTTPX TestClient|
|Deployment|Docker + Docker Compose|

\---

## 📁 Project Structure

```
job-tracker-api/
├── app/
│   ├── models/
│   │   └── models.py          # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py         # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py            # Auth endpoints
│   │   ├── applications.py    # Job application CRUD
│   │   └── interviews.py      # Interview CRUD
│   ├── services/
│   │   ├── auth\_service.py    # JWT + password hashing
│   │   ├── email\_service.py   # Email sending logic
│   │   └── scheduler.py      # Background reminder jobs
│   ├── templates/
│   │   └── index.html         # Frontend dashboard
│   ├── config.py              # App settings (pydantic-settings)
│   └── database.py            # DB engine + session
├── tests/
│   └── test\_api.py            # Unit + integration tests
├── main.py                    # FastAPI app entrypoint
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pytest.ini
├── .env.example
└── .gitignore
```

\---

## ⚡ Quick Start

### Option A — Docker (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR\_USERNAME/job-tracker-api.git
cd job-tracker-api

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your email credentials

# 3. Start everything
docker compose up --build

# API is live at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Option B — Local (without Docker)

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\\Scripts\\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env — set DB\_HOST=localhost and your credentials

# 4. Create MySQL database
mysql -u root -p
CREATE DATABASE job\_tracker\_db;
CREATE USER 'jobtracker'@'localhost' IDENTIFIED BY 'jobtracker\_password';
GRANT ALL PRIVILEGES ON job\_tracker\_db.\* TO 'jobtracker'@'localhost';
FLUSH PRIVILEGES;

# 5. Run the app (tables auto-created on startup)
uvicorn main:app --reload
```

\---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
SECRET\_KEY=your-super-secret-key
DB\_HOST=localhost
DB\_USER=jobtracker
DB\_PASSWORD=jobtracker\_password
DB\_NAME=job\_tracker\_db

# Gmail SMTP example
MAIL\_USERNAME=your-email@gmail.com
MAIL\_PASSWORD=your-app-password    # Use Gmail App Password, not your real password
MAIL\_FROM=your-email@gmail.com
```

> \*\*Gmail tip:\*\* Go to Google Account → Security → 2-Step Verification → App Passwords to generate one.

\---

## 📖 API Endpoints

### Auth

|Method|Endpoint|Description|Auth|
|-|-|-|-|
|POST|`/api/auth/register`|Register a new user|❌|
|POST|`/api/auth/login`|Login, get JWT token|❌|
|GET|`/api/auth/me`|Get current user profile|✅|
|PATCH|`/api/auth/me`|Update profile/settings|✅|

### Job Applications

|Method|Endpoint|Description|Auth|
|-|-|-|-|
|POST|`/api/applications/`|Create a new application|✅|
|GET|`/api/applications/`|List applications (filter/paginate)|✅|
|GET|`/api/applications/stats`|Get status counts|✅|
|GET|`/api/applications/{id}`|Get a single application|✅|
|PATCH|`/api/applications/{id}`|Update an application|✅|
|DELETE|`/api/applications/{id}`|Delete an application|✅|

### Interviews

|Method|Endpoint|Description|Auth|
|-|-|-|-|
|POST|`/api/applications/{id}/interviews/`|Add an interview|✅|
|GET|`/api/applications/{id}/interviews/`|List interviews|✅|
|PATCH|`/api/applications/{id}/interviews/{iid}`|Update an interview|✅|
|DELETE|`/api/applications/{id}/interviews/{iid}`|Delete an interview|✅|

\---

## 🧪 Running Tests

Tests use an **in-memory SQLite database** — no MySQL required.

```bash
pytest -v
```

Expected output:

```
tests/test\_api.py::test\_register\_success           PASSED
tests/test\_api.py::test\_register\_duplicate\_email   PASSED
tests/test\_api.py::test\_login\_success              PASSED
tests/test\_api.py::test\_login\_wrong\_password       PASSED
tests/test\_api.py::test\_get\_me                     PASSED
tests/test\_api.py::test\_create\_application         PASSED
tests/test\_api.py::test\_list\_applications          PASSED
tests/test\_api.py::test\_filter\_by\_status           PASSED
tests/test\_api.py::test\_update\_application         PASSED
tests/test\_api.py::test\_delete\_application         PASSED
tests/test\_api.py::test\_stats\_endpoint             PASSED
tests/test\_api.py::test\_unauthorized\_access        PASSED
tests/test\_api.py::test\_create\_interview           PASSED
tests/test\_api.py::test\_health\_check               PASSED
```

\---

## 📊 Application Statuses

|Status|Description|
|-|-|
|`wishlist`|Saved for later, not yet applied|
|`applied`|Application submitted|
|`interview`|Interview scheduled or ongoing|
|`offer`|Received a job offer|
|`rejected`|Application was rejected|
|`withdrawn`|You withdrew the application|

\---

## 📧 Email Reminders

When `email\_reminders` is enabled on your account (default: on):

* **Follow-up reminders** — sent when a `follow\_up\_date` is within the next 24 hours
* **Interview reminders** — sent 24 hours before a scheduled interview

The scheduler checks every 6–12 hours automatically in the background.

\---

## 🌐 Frontend

A basic HTML/CSS/JS dashboard is served at `http://localhost:8000/`. It supports:

* Register \& login
* View stats by status
* Add, edit, delete applications
* Filter by status and search by company
* 

