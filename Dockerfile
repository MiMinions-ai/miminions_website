# Use an official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies (assumes requirements.txt exists)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5010

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port", "5010"]
