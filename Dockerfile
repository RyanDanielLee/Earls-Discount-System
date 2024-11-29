# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app/Earls_Discount_System/Earls_Discount_System

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Download and install Cloud SQL Auth Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /cloud_sql_proxy \
    && chmod +x /cloud_sql_proxy

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the application code
COPY . .

# Collect static files during build (instead of at runtime)
RUN cd Earls_Discount_System && python manage.py collectstatic --noinput

# Run pytest for testing
RUN cd Earls_Discount_System && pytest --ds=Earls_Discount_System.settings --maxfail=5 --disable-warnings || true

# Expose port 8080 for the application to run on
EXPOSE 8080

# Set the environment variable for Django settings
ENV DJANGO_SETTINGS_MODULE=Earls_Discount_System.settings

# Start Cloud SQL Auth Proxy and Gunicorn for Django
CMD /cloud_sql_proxy -instances=bcit-ec:us-west1:card-issuer=tcp:3306 & \
    cd Earls_Discount_System && gunicorn --bind 0.0.0.0:$PORT Earls_Discount_System.wsgi:application
    
# Run the Django development server
# CMD ["sh", "-c", "/cloud_sql_proxy -instances=bcit-ec:us-west1:card-issuer=tcp:3306 & cd Earls_Discount_System && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:$PORT Earls_Discount_System.wsgi:application"]