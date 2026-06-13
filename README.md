# 🏛️ BUET Civil — Major-Minor Selection System

A web application for the **Bangladesh University of Engineering and Technology (BUET) Civil Engineering Department** to manage the allocation of Major, Minor, and Thesis Supervisor for 4th-year students.

Students submit ranked preferences for (Major+Minor) combinations and supervisors. A rank-based greedy algorithm allocates seats fairly — higher-ranked students get priority.

---

## 📚 Domain Background

The 4th-year Civil Engineering curriculum is divided into **4 specialities**:

| Code | Speciality |
|------|-----------|
| **S** | Structure |
| **T** | Transport |
| **E** | Environment |
| **G** | Geotech |

Each student selects **two** specialities — one **Major** and one **Minor**. The student must complete all coursework in their Major. They also choose a **supervisor** under whom they will perform their thesis.

### Constraint Summary

| Constraint | Source |
|---|---|
| Each (Major+Minor) combo has a fixed number of seats | **List Two** (admin uploads) |
| Each supervisor takes a fixed number of students | **List One** (admin uploads) |
| Students are ranked by merit | **List Three** (admin uploads) |

### Allocation Logic

1. Students are sorted by merit rank (ascending)
2. Each student's combo preferences are iterated in priority order
3. For each combo, the system checks seat availability AND supervisor availability
4. The **first available** combo + supervisor pair is assigned
5. Unranked combos are treated as equal-lowest priority (sorted alphabetically)

---

## ✨ Features

### 👨‍🎓 Student Portal
- **Login / Registration** — Student ID + password. New IDs auto-register.
- **✅ Student ID Validation** — IDs must be exactly 7 digits and start with a configurable prefix (default: `2104`).
- **📌 My Allocation** — Real-time view of your assigned combo and supervisor.
- **⚙️ Preferences** — Interactive dropdowns to rank combos (1–12) and supervisors per major.
- **📊 Results Table** — Searchable, sortable table of all students' allocations with autocomplete suggestions.

### 🔐 Admin Panel
- **Secure Login** — Username/password authentication.
- **👤 Supervisors (List One)** — Add/edit/delete supervisor assignments per major. CSV import/export.
- **📋 Combo Seats (List Two)** — Configure seat limits for each major+minor combination. CSV import (`ST,27` format) / export.
- **🏆 Merit List (List Three)** — Upload ranked student list via CSV (`rank,student_id`). Manual add/remove. Auto-creates student accounts.
- **👥 Student Management** — View all registered students, reset passwords.
- **▶️ Auto-Allocation** — Runs automatically whenever data changes (preferences, seats, or ranks update).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# 1. Clone the repository
git clone <repo-url> && cd MajorSelectionBUET

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env to set your SECRET_KEY, admin credentials, and STUDENT_ID_PREFIX

# 4. Run (development)
python app.py
```

The app will be available at **http://127.0.0.1:5000**.

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ Change these immediately in `.env` for any production deployment.

---

## 🏭 Production Deployment

### Gunicorn (recommended)

```bash
# Direct
gunicorn wsgi:app -c gunicorn_config.py

# With custom workers / port
GUNICORN_WORKERS=8 GUNICORN_BIND=0.0.0.0:8000 gunicorn wsgi:app -c gunicorn_config.py
```

### systemd Service (persistent)

```bash
sudo cp deploy/buet-major-selection.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable buet-major-selection
sudo systemctl start buet-major-selection

# View logs
sudo journalctl -u buet-major-selection -f
```

### One-shot Deploy

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

### Production Checklist

- [ ] Set `PRODUCTION=true` in `.env`
- [ ] Set a strong `SECRET_KEY`
- [ ] Change default admin password
- [ ] Set `DATABASE_URI` to an **absolute path**: `sqlite:////absolute/path/to/instance/major_selection.db`
- [ ] Set `STUDENT_ID_PREFIX` to match your department's intake (e.g., `2104` for 2021 intake, dept 04)
- [ ] Configure `SERVER_NAME` to your domain
- [ ] Set up nginx reverse proxy (see below)

### nginx Reverse Proxy (recommended)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/hamim-mahmud/Workspace/MajorSelectionBUET/static/;
        expires 30d;
    }
}
```

---

## 🗄️ Project Structure

```
MajorSelectionBUET/
├── app.py                    # Flask app factory, entry point
├── wsgi.py                   # WSGI entry point for gunicorn/uvicorn
├── config.py                 # Configuration (reads from .env)
├── gunicorn_config.py        # Gunicorn production settings
├── Procfile                  # Platform deploy (Heroku, etc.)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (git-ignored)
│
├── models/
│   └── __init__.py           # SQLAlchemy models (7 tables)
│
├── routes/
│   ├── auth_bp.py            # Student login/signup
│   ├── admin_bp.py           # Admin CRUD + CSV import/export
│   ├── dashboard_bp.py       # Student dashboard (3 sections)
│   └── api_bp.py             # AJAX endpoints (preferences, search)
│
├── services/
│   └── allocator.py          # Greedy rank-based allocation algorithm
│
├── templates/
│   ├── base.html             # Base layout (Tailwind CSS)
│   ├── login.html            # Student login page
│   ├── admin/
│   │   ├── login.html        # Admin login
│   │   ├── dashboard.html    # Admin dashboard with stats
│   │   ├── supervisors.html  # List One CRUD
│   │   ├── combos.html       # List Two CRUD
│   │   ├── merit.html        # List Three CRUD
│   │   └── students.html     # Student management
│   └── dashboard/
│       └── index.html        # Student dashboard (3 sections)
│
├── static/
│   └── js/
│       ├── preferences.js    # Combo + supervisor preference saving
│       └── search.js         # Real-time search with autocomplete
│
└── deploy/
    ├── buet-major-selection.service   # systemd service unit
    └── deploy.sh                      # One-shot deployment script
```

---

## 🗄️ Database Schema

| Table | Purpose | Key Columns |
|---|---|---|
| `admin` | Admin accounts | `username`, `password_hash` |
| `student` | Student accounts | `id` (student_id PK), `password_hash`, `rank` |
| `supervisor` | List One — supervisor capacity | `name`, `major_code` (S/T/E/G), `seats` |
| `combo_seat` | List Two — combo seat limits | `major_code`, `minor_code`, `seats` |
| `student_combo_pref` | Student combo rankings | `student_id`, `major_code`, `minor_code`, `priority` |
| `student_supervisor_pref` | Student supervisor rankings | `student_id`, `supervisor_id`, `major_code`, `priority` |
| `allocation` | Final allocation results | `student_id`, `major_code`, `minor_code`, `supervisor_id` |

---

## 🔧 Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key` | Flask session signing key |
| `FLASK_ENV` | `development` | `development` or `production` |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `admin123` | Default admin password |
| `DATABASE_URI` | `sqlite:///major_selection.db` | SQLAlchemy database URI |
| `STUDENT_ID_PREFIX` | `2104` | First 4 digits all student IDs must start with |
| `PRODUCTION` | `false` | Enables secure cookies, disables debug |
| `SERVER_NAME` | — | Production domain name |
| `PORT` | `5000` | Dev server port |

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/preferences/combo` | Save combo priority list |
| `POST` | `/api/preferences/supervisor` | Save supervisor priority list for a major |
| `GET` | `/api/allocation/status` | Get current user's allocation as JSON |
| `GET` | `/api/search?q=...&filter=...` | Search allocations (student_id or combo) |
| `GET` | `/api/search/suggestions?q=...&filter=...` | Autocomplete suggestions |

---

## ✅ Testing the System

### Manual Test Flow

1. **Admin Setup**
   - Login as admin (`admin` / `admin123`)
   - Go to **Supervisors** → add supervisors with seat counts
   - Go to **Combos** → add major-minor combos with seat limits
   - Go to **Merit List** → upload a CSV of ranked students

2. **Student Registration**
   - Go to login page → enter a valid 7-digit Student ID starting with the prefix
   - Set a password → redirected to dashboard
   - Use dropdowns to rank combo and supervisor preferences → save

3. **Verify Allocation**
   - The allocation runs automatically on save
   - Check "My Allocation" section to see assigned combo + supervisor
   - Check the "Allocation Results" table to see all students

### CSV Formats

**Supervisors (List One):**
```csv
name,major,seats
Amanat Sir,S,4
Tahsin Sir,S,4
Shamsul Sir,T,4
```

**Combos (List Two):**
```csv
ST,27
SG,27
SE,27
TS,13
```

**Merit List (List Three):**
```csv
1,2104065
2,2104053
3,2104122
```

---

## 🧠 Architecture Decisions

- **Allocation Algorithm**: Greedy by rank (simplest, matches real-world "higher rank gets priority").
- **Auto-Allocation**: Runs on every data change — preferences, seats, or ranks update.
- **Supervisor per Major**: One supervisor preference list per major, shared across all combos containing that major.
- **Partial Preferences**: If a student ranks only 3 out of 12 combos, the remaining 9 get equal-lowest priority (sorted alphabetically).
- **Tailwind CSS**: Via CDN (no build step needed).
- **Vanilla JavaScript**: Keeps the frontend lightweight — no framework overhead.

---

## 📄 License

This project is licensed under the terms included in the `LICENSE` file.
