# Olive MMS — Deploy to Render.com

> This project ships with Render deployment files in the repo root: `render.yaml`
> (Blueprint), `build.sh`, `run.sh`, `Dockerfile`, and `.dockerignore`.
> Stack: **Django + PostgreSQL**, served with **Gunicorn**; static files via
> **WhiteNoise**. No Redis/Celery — nothing extra to run.

---

## 1. What the deploy does

| File | Purpose |
|------|---------|
| `render.yaml` | Blueprint: a free **PostgreSQL 15** service + one **web service** |
| `build.sh` | `pip install -r requirements.txt` + `python manage.py collectstatic --noinput` |
| `run.sh` | `migrate` → create superuser (if env vars set) → `gunicorn config.wsgi` |
| `Dockerfile` | Optional container image (`python:3.11-slim`); used if you pick the Docker runtime |
| `.dockerignore` | Keeps `.venv`, `media`, `staticfiles`, env files out of the image |

Production settings (`config/settings/prod.py`) enable HTTPS security defaults:
`SECURE_SSL_REDIRECT`, secure session/CSRF cookies, and HSTS. `ALLOWED_HOSTS` is
read from the `DJANGO_ALLOWED_HOSTS` env var.

---

## 2. Prerequisites

- A GitHub (or GitLab) repo containing this project, e.g. `shajeebsh/olive_mms`.
- A [Render.com](https://render.com) account.
- Recommended: push to a stable branch first, then connect Render to it.

---

## 3. Deploy with the Blueprint (recommended)

1. Push the repo to GitHub (includes `render.yaml`).
2. In Render: **New + → Blueprint**.
3. Select the repository and branch.
4. Render reads `render.yaml` and provisions:
   - `olive-mms-db` — PostgreSQL 15 (free).
   - `olive-mms-web` — web service; build runs `./build.sh`, start runs `./run.sh`.
5. Click **Apply** (blueprint) / **Deploy**.

That's it — the first deploy runs migrations automatically via `run.sh`.

### After first deploy
- Set a superuser (see §5) and finish the mosque setup wizard at the app URL.
- Go to **olive-mms-web → Settings → Environment** to view the generated
  `DJANGO_SECRET_KEY` and the auto-linked `DATABASE_URL`.

---

## 4. Deploy manually (no Blueprint)

Use this if you removed `render.yaml`.

1. **New + → PostgreSQL** — create `olive-mms-db` (free). Note its **Internal
   Database URL**.
2. **New + → Web Service** — select the repo/branch.
3. Set **Build Command**: `./build.sh`
4. Set **Start Command**: `./run.sh`
5. Add these environment variables:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | click **Generate** (long random string) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `olive-mms-web.onrender.com` (add custom domains, comma-separated) |
| `DATABASE_URL` | paste the Postgres **Internal Database URL** from step 1 |
| `DJANGO_SUPERUSER_EMAIL` | e.g. `admin@example.com` (optional, see §5) |
| `DJANGO_SUPERUSER_PASSWORD` | strong password (optional, see §5) |

6. **Create Web Service** and wait for the first deploy to finish.

> Tip: prefer **Docker** runtime? Set the web service runtime to Docker — Render
> builds the `Dockerfile` and runs `CMD ["./run.sh"]` automatically.

---

## 5. Creating an admin/superuser

`run.sh` creates a superuser on every start **iff** `DJANGO_SUPERUSER_EMAIL` and
`DJANGO_SUPERUSER_PASSWORD` are both set and that email doesn't already exist.
It's easiest to set them **before the first deploy**, then remove the password
afterwards.

To create one after deploy:

```
Render → olive-mms-web → Shell
python manage.py createsuperuser
```

Log in at `https://<your-app>.onrender.com/admin/`.

---

## 6. First-run checklist (after deploy)

- [ ] `https://<app>.onrender.com/` loads the login page (HTTPS enforced).
- [ ] Static assets (theme CSS/JS, favicon) load — served by WhiteNoise from
      `collectstatic`.
- [ ] Login with the superuser, then run the **institution setup** to set the
      mosque profile.
- [ ] Optional: seed demo data with `python manage.py seed_demo` (from the Render
      shell).
- [ ] Dashboard and all module pages render without 500s.

---

## 7. Updating the deployed app

Render auto-deploys on every push to the connected branch (same build/start
commands). `run.sh` runs `migrate` on each start, so new migrations apply
automatically.

---

## 8. Custom domain

1. **olive-mms-web → Settings → Custom Domains** → add `mms.example.org`.
2. Add the domain to `DJANGO_ALLOWED_HOSTS`
   (e.g. `olive-mms-web.onrender.com,mms.example.org`).
3. Point your DNS (CNAME → `<service>.onrender.com`) as Render instructs.
4. HTTPS certificate is issued automatically.

---

## 9. Known limitations / notes

- **Free tier**: web services sleep after ~15 min of inactivity (first request
  after a sleep causes a cold start of a few seconds). Free Postgres databases
  are paused/deleted per Render's current free-tier policy — keep that in mind
  for real data.
- **Local disk is ephemeral**: `MEDIA_ROOT` is the container's filesystem
  (`media/`), which is wiped on each redeploy. The app currently has no
  user-upload features, so this is fine; if uploads are added later, switch
  `default` storage in `STORAGES` to an object store (e.g. S3).
- **Environment safety**: never put the real `DJANGO_SECRET_KEY` in the repo;
  Render's `generateValue: true` handles it. Use `python manage.py check
  --deploy` locally to audit production settings.
- **Workers**: 3 gunicorn workers on a free instance is generous for this
  lightweight app; lower it if you hit memory limits (Render free instances have
  512 MB).

---

## 10. Local verification before deploying

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_SECRET_KEY="<a-long-random-value>" DJANGO_ALLOWED_HOSTS="localhost"
python manage.py check --deploy --settings=config.settings.prod   # prod settings
python manage.py collectstatic --noinput                          # what build.sh does
```
