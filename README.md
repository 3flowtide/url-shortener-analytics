# URL Shortener with Click Analytics

A URL shortener with a REST API and a small web dashboard. Click analytics
(device, browser, referrer) are processed asynchronously through a
Pub/Sub-triggered Cloud Function, so the redirect itself stays fast.

## Tech stack

Python, Flask, SQLAlchemy, PostgreSQL (SQLite for local dev), Docker, and
Google Cloud (Cloud Run, Cloud SQL, Pub/Sub, Cloud Functions).

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

python run.py
```

Visit `http://localhost:8080` for the dashboard, or use the API directly:

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "hunter22"}'

curl -X POST http://localhost:8080/api/links \
  -H "Authorization: Bearer <api_token>" \
  -H "Content-Type: application/json" \
  -d '{"long_url": "https://example.com/some/long/path"}'
```

## Running with Docker

```bash
docker build -t url-shortener .
docker run -p 8080:8080 --env-file .env url-shortener
```

## API

| Method | Path                        | Description                 |
|--------|-----------------------------|-------------------------------|
| POST   | `/api/auth/register`        | Create an account             |
| POST   | `/api/auth/login`           | Log in                        |
| POST   | `/api/links`                | Create a short link           |
| GET    | `/api/links`                | List your short links         |
| DELETE | `/api/links/<id>`           | Deactivate a short link       |
| GET    | `/api/links/<id>/analytics` | Click analytics for a link    |
| GET    | `/<code>`                   | Redirect and record a click   |

## Deploying to Google Cloud

```bash
PROJECT_ID=your-project-id REGION=us-central1 ./scripts/deploy.sh
```

Provisions Cloud SQL, a Pub/Sub topic, Cloud Run, and the Cloud Function.
Requires the `gcloud` CLI authenticated against a billing-enabled project.

## Tests

```bash
pytest tests/
```
