FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install --retries 5 --timeout 60 -r requirements.txt

# Expose the Flask port
EXPOSE 5000

# Set environment variable for Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Run the app
CMD ["flask", "run", "--host=0.0.0.0"]
