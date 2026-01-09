# miminions.ai

The official web application for [miminions.ai](https://miminions.ai) - an open-source framework for creating, deploying, and managing agentic AI systems at scale.

## Overview

miminions.ai is a powerful framework that enables developers to build autonomous AI agents that can think, plan, and execute tasks independently.

## Features

- **Agentic AI Framework**: Build autonomous AI agents that think, plan, and execute
- **User Authentication**: Secure login/signup with Flask-Login and JWT
- **AI Assistant Management**: Create and manage AI assistants
- **Real-time Chat Interface**: Interactive chat with AI agents
- **File Upload & Management**: Handle files with AWS S3 integration
- **Docker Support**: Easy containerized deployment

## Tech Stack

- **Backend**: Flask, Python
- **Authentication**: Flask-Login, JWT
- **AI Integration**: OpenAI, FAISS, Sentence Transformers
- **Storage**: AWS S3
- **Frontend**: Jinja2 templates, CSS, JavaScript
- **Containerization**: Docker

## Project Structure

```
website/
├── apps/                  # Application modules (API, database, storage)
├── static/                # Static assets (CSS, JS, images)
├── templates/             # Jinja2 HTML templates
├── Documentation/         # Project documentation
├── s3uploads/             # File upload directory
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
└── docker-compose.yml     # Docker Compose configuration
```

## Quick Start

### Local Development

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
   python run.py
   ```

### Docker Deployment

```bash
docker-compose up --build
```

## Environment Variables

See `example.env` for required configuration:

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT authentication secret
- AWS credentials (for S3 file storage)
- OpenAI API key (for AI features)

## API Endpoints

- `/apilogin`: API authentication
- `/assistants`: Assistant management (CRUD)
- `/threads`: Thread management
- `/attach_file`: File attachment endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

Built with ❤️ by the miminions.ai team