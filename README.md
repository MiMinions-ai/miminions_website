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
   # Edit .env with your SECRET_KEY and AWS credentials
   ```

2. Run the application:
   ```bash
   python application.py
   ```
   
   The application will use local JSON database (`users_local_db.json`) when `FLASK_ENV` is not set to `production`.
   
   You can also use the `--test` flag for explicit test mode:
   ```bash
   python application.py --test
   ```
   
   Visit http://localhost:5000

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key for sessions |
| `FLASK_ENV` | Yes | Set to `production` for AWS DynamoDB, or `local` for local JSON database |
| `AWS_REGION` | Production | AWS region (default: `us-east-2`) |
| `AWS_ACCESS_KEY_ID` | Local only | AWS credentials for local dev |
| `AWS_SECRET_ACCESS_KEY` | Local only | AWS credentials for local dev |

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

## License

MIT License
