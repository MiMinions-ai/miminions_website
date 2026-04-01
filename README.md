# miminions.ai

The official website for [miminions.ai](https://miminions.ai) — an open-source framework for autonomous AI agents.

## Tech Stack

- **Backend:** Flask, Python 3.10+
- **Auth:** Flask-Login, Flask-WTF (CSRF)
- **Database:** AWS DynamoDB
- **Deployment:** AWS Elastic Beanstalk

## Project Structure

```
miminions_website/
├── apps/
│   ├── database.py        # DynamoDB connection
│   └── store.py           # User data operations
├── static/
│   ├── css/               # Stylesheets
│   └── images/            # Static images
├── templates/             # Jinja2 HTML templates
├── application.py         # Flask application entry point
├── requirements.txt       # Python dependencies
├── Procfile               # Gunicorn config for EB
└── example.env            # Environment variable template
```

## Local Development

1. **Clone and set up a virtual environment:**
   ```bash
   git clone https://github.com/miminions-ai/miminions_website.git
   cd miminions_website
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp example.env .env
   # Edit .env with your SECRET_KEY and other values
   ```

4. **Run the application:**
   ```bash
   python application.py
   ```
   
   Runtime mode summary:
   - `FLASK_ENV=production` uses AWS DynamoDB.
   - Any non-production value (for example `local`) uses local JSON-backed storage.
   
   Command flags:
   - `--test` forces testing config.
   - `--local` forces local/dev behavior even if `FLASK_ENV=production` is set.

   Example:
   ```bash
   python application.py --test
   ```
   
   Visit http://localhost:5000

## Testing and Quality

Run the test suite:

```bash
pytest
```

Run lint and formatting checks:

```bash
ruff check .
black --check .
```

The repository includes a CI workflow at `.github/workflows/ci.yml` that runs:

- Ruff lint checks
- Black formatting checks
- Pytest test suite
- Dependency vulnerability scan via `pip-audit`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key for sessions |
| `FLASK_ENV` | Yes | Set to `production` for AWS DynamoDB, or `local` for local JSON database |
| `AWS_REGION` | Production | AWS region (default: `us-east-2`) |
| `JWT_SECRET_KEY` | Yes | Secret key for JWT email verification tokens |
| `RESEND_API_KEY` | Yes | API key for Resend email service |
| `MAIL_FROM` | Yes | Sender email address for Resend |
| `CONTACT_EMAIL` | Yes | Recipient email address for contact form |
| `REDIS_URL` | Production recommended | Redis backend for Flask-Limiter storage |

Local email behavior:

- If `RESEND_API_KEY` is not set in local/dev mode, the app skips real email sends and logs a development message.
- Signup and contact flows still return success paths so local development is not blocked by email setup.

On AWS Elastic Beanstalk / EC2, IAM roles provide credentials automatically.

## AWS Resources

- **DynamoDB Table:** `users` (partition key: `email`)
- **IAM Role:** EB instance profile with `AmazonDynamoDBFullAccess`

## Deployment (Elastic Beanstalk)

```bash
pip install awsebcli
eb init -p python-3.10 miminions-app
eb create miminions-prod
eb deploy
```

Set environment variables via the EB Console under Configuration → Software.

## Observability

The app now emits request-correlated logs and response headers:

- `X-Request-ID` is accepted from incoming requests (or generated if missing)
- `X-Request-ID` is returned in every response
- Log lines include `req:<request_id>` for easier tracing across auth, email, and DynamoDB events

## Incident Runbook

Auth failures:

1. Check logs for `Login failed` and `Signup failed` entries with request IDs.
2. Verify `SECRET_KEY`, `JWT_SECRET_KEY`, and cookie settings.
3. Confirm limiter backend is healthy if users are unexpectedly throttled.

Email delivery failures:

1. Check logs for `Failed to send verification email` or `Failed to send contact email`.
2. Verify `RESEND_API_KEY`, `MAIL_FROM`, and sender domain verification in Resend.
3. Retry with a known-good recipient and compare request IDs.

DynamoDB failures:

1. Check `/health` and application logs for DynamoDB retry/error entries.
2. Verify IAM permissions and `AWS_REGION` configuration.
3. Confirm table schema (`users`, partition key `email`) is unchanged.

## Deployment Checklist

Before deploying:

1. Confirm required environment variables are set for the target environment.
2. Ensure `REDIS_URL` is configured in production for persistent limiter state.
3. Run `ruff check .`, `black --check .`, and `pytest` locally or in CI.
4. Validate `/health` in the deployed environment.
5. Spot-check signup/login/contact flows and verify `X-Request-ID` appears in responses and logs.

## Troubleshooting

App fails to start with missing environment variable error:

1. Confirm `.env` exists and includes `SECRET_KEY`.
2. In production, confirm `SECRET_KEY`, `JWT_SECRET_KEY`, `RESEND_API_KEY`, `MAIL_FROM`, and `CONTACT_EMAIL` are set.

Unexpected local mode while testing production settings:

1. Check whether `--local` is present in your startup command.
2. Verify `FLASK_ENV` is explicitly set to `production` in the running environment.

## License

MIT License
