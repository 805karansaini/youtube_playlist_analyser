# Base image: Using slim version of Python 3.12 to minimize container size
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /youtube_playlist_analyser

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies specified in requirements.txt
# --no-cache-dir reduces the image size by not caching pip packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
# The ./app source will be copied to /youtube_playlist_analyser/app
COPY ./app /youtube_playlist_analyser/app

# Security: Create a non-root user for running the application
# --disabled-password: No password authentication
# --gecos '': No additional user information
# chown: Transfer ownership of working directory to the new user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /youtube_playlist_analyser
USER appuser

# Add the application directory to Python path for proper module imports
ENV PYTHONPATH=/youtube_playlist_analyser:/youtube_playlist_analyser/app

# Start the application using gunicorn server
# Bind to all interfaces on port 5001
# Use app.main:app as the WSGI application entry point
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app.main:app"]
