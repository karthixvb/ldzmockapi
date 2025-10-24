FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all source code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Start Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app_fast:app"]
