# 🦷 DentaFlow

A solo-dentist **appointment manager** — smart slot suggestions, reschedule/cancel,
follow-ups & recalls, and one-tap pre-filled WhatsApp reminders. Built with Streamlit
+ Postgres, deployable free on Streamlit Community Cloud.

See [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) for the product scope.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

- With no secrets configured, it uses a local SQLite file (`dentaflow.db`) and the
  password **`dentist`** — good enough for local development.
- Run the tests: `.venv/bin/pytest`

## Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (gitignored) and set:

```toml
db_url = "postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
app_password = "your-strong-password"
```

## Get a free Postgres (Neon or Supabase)

1. Create a free project at [neon.tech](https://neon.tech) or [supabase.com](https://supabase.com).
2. Copy the connection string. Ensure it uses the `postgresql+psycopg://` prefix and
   `?sslmode=require`.
3. Put it in `db_url` (locally in `secrets.toml`, in production in the Streamlit
   Secrets UI). Tables are created automatically on first run.

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create an app pointing at
   `app.py`.
3. In the app's **Settings → Secrets**, paste `db_url` and `app_password`.
4. Deploy. Because data lives in managed Postgres, it **survives every redeploy/restart**.

## How it works

- **Data** — `patients`, `appointments`, `availability_blocks`, `settings`
  (see `lib/db.py`). Reads are uncached (tiny data volume) for always-fresh state.
- **Smart Slot Suggestions** — pure, tested logic in `lib/scheduler.py`: only inside
  clinic sessions, never in blocked time, fits duration+buffer, clusters onto days you
  already work, centers follow-ups on their interval, respects your daily cap.
- **WhatsApp** — `lib/whatsapp.py` builds `wa.me` deep links with the message
  pre-filled; you tap send. No WhatsApp API, no cost.
- **Screens** — `views/` (Today, Week, Book, Patients, Availability, Reminders, Settings),
  routed from `app.py` behind a single password gate.

## Notes

- **English only**, single practitioner, no patient-facing surface (you control everything).
- Requires connectivity (it's a hosted app — no offline mode).
- Store minimal patient data; the app is password-gated and DB credentials live only in
  secrets (aligns with India's DPDP Act 2023).
