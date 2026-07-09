# Deploying VehicleGrade

Backend on Railway (Flask + Postgres), frontend on Vercel (Next.js), domain on Spaceship.
Everything below is copy-paste steps for the parts that only exist inside each dashboard.

---

## 1. Railway — backend

1. **Create project**: [railway.app](https://railway.app) → New Project → Deploy from GitHub repo → select this repo.
2. **Set the root directory**: in the new service's Settings → set **Root Directory** to `backend`.
3. **Add Postgres**: in the project, click **+ New** → **Database** → **PostgreSQL**. Railway auto-injects a `DATABASE_URL` env var into the project — the backend service needs a *reference* to it:
   - Go to the backend service → **Variables** → add `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (Railway's variable-reference syntax; pick the Postgres service from the dropdown it offers).
4. **Set the remaining env vars** on the backend service (Variables tab):
   ```
   FLASK_ENV=production
   FLASK_DEBUG=false
   ALLOWED_ORIGINS=https://vehiclegrade.ca,https://www.vehiclegrade.ca
   ```
   Leave `LLM_PROVIDER` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` unset until you actually have a key — the app works fully without them.
5. **Deploy**. Railway detects `backend/Procfile` and runs `gunicorn wsgi:app`. It sets `PORT` itself; `run.py`/`wsgi.py` already read it.
6. **Seed the database** (one-time, after the first successful deploy): open a shell on the Railway service (Service → the "..." menu → **Shell**, or `railway run` locally with the Railway CLI linked to this service) and run:
   ```
   flask --app run.py seed-db
   ```
   This populates the fresh Postgres instance with all 17 makes' reference data + the seeded listing sample.
7. **Get the public URL**: Railway assigns a `*.up.railway.app` domain automatically — note it, you'll point `api.` at it in step 3 below. In Settings → Networking, add a **Custom Domain**: `api.vehiclegrade.ca`. Railway will show you a CNAME target.

## 2. Vercel — frontend

1. [vercel.com](https://vercel.com) → **Add New** → **Project** → import this same GitHub repo.
2. **Root Directory**: set to `frontend` (Vercel auto-detects Next.js once this is set — no other config needed).
3. **Environment Variables**: add
   ```
   NEXT_PUBLIC_API_URL=https://api.vehiclegrade.ca
   ```
   (Use the Railway `*.up.railway.app` URL here temporarily if DNS isn't live yet, then update it once the domain is pointed.)
4. **Deploy.**
5. **Custom domain**: Project → Settings → Domains → add `vehiclegrade.ca` and `www.vehiclegrade.ca`. Vercel will show the DNS records it needs (see below).

## 3. Spaceship — DNS

In Spaceship's DNS management for the domain, add:

| Type  | Host  | Value                                  |
|-------|-------|-----------------------------------------|
| A     | `@`   | Vercel's IP (shown on Vercel's Domains page, e.g. `76.76.21.21`) |
| CNAME | `www` | `cname.vercel-dns.com`                  |
| CNAME | `api` | the Railway CNAME target from step 1.7  |

DNS propagation can take anywhere from a few minutes to a few hours. Vercel/Railway will show the domain as "verified" once it's live.

## 4. Final step — lock down CORS

Once `vehiclegrade.ca` actually resolves, double check `ALLOWED_ORIGINS` on the Railway backend service matches the real domain exactly (including `https://`, no trailing slash), then redeploy the backend service if you changed it.

---

## Local production sanity checks (already verified this session)

- `pip install -r backend/requirements.txt` installs cleanly.
- `gunicorn wsgi:app` boots and serves real API responses (`psycopg2-binary` needs Postgres client headers to build locally on macOS without Homebrew's `postgresql` installed — this is a local-machine-only limitation; Railway's Linux build environment has prebuilt wheels and installs it without issue).
- `/analyze` returns identical, error-free reports whether or not an LLM key is configured — the `ai_explanation` section is simply absent with no key set.

## What's out of scope for this deployment pass

- The "long tail" of makes beyond the current 17 (Mini, Volvo, Acura, Mitsubishi, Tesla, etc.) — same mechanism (drop a JSON file in `backend/app/utils/vehicle_knowledge_base/`, reseed), can be added incrementally.
- Any LLM provider is optional and inert until you add a key — see `.env.example` for the exact vars.
