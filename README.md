# Adapt Tools

A dockerized Streamlit + MySQL web app to explore climate adaptation tools (FutureMed/COST Action).

## Context

This project was developed as part of the FutureMed COST Action during a short-term scientific mission at CERFACS. It provides a centralized platform for climate adaptation tools, enhancing access and collaboration among researchers and practitioners.

## Features

- Dynamic filters for quickly locating relevant adaptation tools.
- Detailed pages for each tool with comprehensive information.
- Suggestion form to contribute new tools or updates.
- Image upload and management for tool illustrations.
- MySQL backend ensuring robust data storage and retrieval.

---

## What this repo gives you

- **App**: Streamlit UI (filters, tool pages, “suggest a tool”, helper text, etc.).
- **DB**: MySQL schema + an importer that builds the relational database from an Excel file.
- **Web**: Nginx that serves `/assets/*` (images) and reverse‑proxies requests to Streamlit.
- **Docs**: Light guidance for local dev and deployment.

---

## Stack

- **Frontend/App**: Streamlit (Python 3.11)
- **Database**: MySQL 8
- **Web server**: Nginx (serves static assets + reverse proxy)
- **Containers**: Docker Compose

---

## Repo layout

```
adapt-tools/
├─ app/                       # Streamlit app + scripts
│  ├─ app.py                 
│  ├─ scripts/
│  │  └─ build_db_from_excel.py
│  └─ .streamlit/config.toml  # theme and Streamlit settings
├─ public/
│  └─ assets/                 
│     ├─ tools/               # {tool_id}.png thumbnails
│     ├─ tool_banners/        # {tool_id}.png wide banners
│     ├─ logo.png
│     ├─ banner.jpg
│     └─ placeholder.png
├─ data/
│  ├─ samples/                # small sample dataset for demo
│  │  └─ sample_tools.xlsx
│  └─ master/                 # full Excel data (git-ignored)
├─ docs/                      # ARCHITECTURE, DEPLOY, ROADMAP
├─ sql/                       
├─ docker-compose.yml
├─ nginx.conf
├─ requirements.txt
├─ .env.example               # example environment variables
├─ VERSION                   # project version file
├─ dev-build.sh              # build script that handles version injection
└─ .gitignore
```

> **Note:** MySQL data lives in a **Docker volume** (named `adapt-tools_mysql_data`). It’s not stored in the repo; it persists across `docker compose up/down`.

---

## Prerequisites

- Docker Desktop / OrbStack / Colima
- Git, Python not required on host

---

## Versioning

The project version is tracked in the `VERSION` file located at the root of the repository. The provided `dev-build.sh` script reads this version and injects it into the Docker build process. The app footer displays both the current version and the git commit hash to help identify the running build.

To update the project version, simply edit the `VERSION` file with the new version string before building the Docker images.

---

## 1) Configure environment

Create your local `.env` from the example:

```bash
cp .env.example .env
# edit .env and set DB_NAME, DB_USER, DB_PASSWORD, MYSQL_ROOT_PASSWORD
```

These variables are used by both the **app** (to connect) and **MySQL** (to create the DB/user).

---

## 2) Start the stack

Run the provided build script to ensure Docker images are rebuilt with the current version, then start the stack:

```bash
bash dev-build.sh && docker compose up -d
```

- App (Streamlit) runs behind Nginx.
- Nginx serves at **http://localhost:8080/**
- phpMyAdmin (optional) at **http://localhost:8081/**

Health checks:
- App: `http://localhost:8080/_stcore/health` (should return `ok`)

---

## 3) Seed the database

You have two choices:

### Option A — Use the small **sample** Excel (provided)

```bash
docker compose exec \
  -e EXCEL_PATH=/app/data/samples/sample_tools.xlsx \
  app python app/scripts/build_db_from_excel.py
```

### Option B — Request **full** master Excel (atsilimigkras1@tuc.gr)

Place full Excel at `data/master/db_ready_master_cca_tools.xlsx`, then:

```bash
docker compose exec \
  -e EXCEL_PATH=/app/data/master/db_ready_master_cca_tools.xlsx \
  app python app/scripts/build_db_from_excel.py
```

> The importer **drops & recreates** the schema each run, then loads Tools + all link tables and creates the `view_tools_full` view.

---

## 4) Open the app

- **http://localhost:8080/** — main UI
- Images are served at **/assets/** (e.g., `/assets/banner.jpg`).

---

## Development tips

- App logs: `docker compose logs -f app`
- Nginx logs: `docker compose logs -f web`
- DB shell:

  ```bash
  docker compose exec mysql mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME"
  ```

- Rebuild only the app image after code changes:

  ```bash
  docker compose build app && docker compose up -d
  ```

- Re-run the importer with a different Excel:

  ```bash
  docker compose exec -e EXCEL_PATH=/app/data/samples/sample_tools.xlsx app \
    python app/scripts/build_db_from_excel.py
  ```

---

## Deployment (very short)

- Bind Nginx to port **80/443** on a VPS.
- Put the same `.env` there (but with production passwords).
- Optionally terminate TLS in Nginx (or in a reverse proxy like Caddy/Traefik).
- Persist `/var/lib/mysql` via the `mysql_data` named volume (already configured).

See **docs/DEPLOY.md** for details.

---

## License

Apache-2.0