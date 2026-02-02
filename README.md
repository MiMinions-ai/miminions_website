# miminions.ai

The official web application for miminions.ai - an open-source framework for creating, deploying, and managing agentic AI systems at scale.

## Features

- User Authentication with Flask-Login and JWT
- AI Assistant Management via OpenAI API
- Real-time Chat Interface
- File Upload to AWS S3

## Tech Stack

- Backend: Flask, Python 3.10+
- Authentication: Flask-Login, Flask-JWT-Extended
- AI: OpenAI Assistants API
- Database: AWS DynamoDB
- Storage: AWS S3
- Deployment: AWS Elastic Beanstalk

## Project Structure

```
miminions_website/
├── apps/                  # Application modules
│   ├── api.py             # OpenAI API integration
│   ├── database.py        # DynamoDB connection
│   └── store.py           # Database operations
├── static/                # Static assets (CSS, JS, images)
├── templates/             # Jinja2 HTML templates
├── .ebextensions/         # Elastic Beanstalk configuration
├── application.py         # Flask application entry point
├── requirements.txt       # Python dependencies
└── example.env            # Environment variables template
```

## Local Development

1. **Clone and setup**:
```bash
git clone https://github.com/miminions-ai/miminions_website.git
cd miminions_website
python -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp example.env .env
# Edit .env with your configuration
```

4. **Run the application**:
```bash
python application.py
```
Visit http://localhost:5000

## AWS Elastic Beanstalk Deployment

1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init -p python-3.10 miminions-app`
3. Create environment: `eb create miminions-prod`
4. Configure environment variables in AWS Console
5. Deploy: `eb deploy`

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | JWT authentication secret |
| `AWS_REGION` | AWS region (e.g., us-east-1) |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `S3_BUCKET` | S3 bucket name |
| `S3_REGION` | S3 bucket region |
| `LOCAL_UPLOAD_FOLDER` | Local temp folder (./uploads) |

## AWS Resources Required

- **DynamoDB Tables**: users, assistants, user_threads, user_messages, vector_files
- **S3 Bucket**: For file uploads
- **IAM Role**: EB instance role with DynamoDB and S3 permissions

## License

MIT License
