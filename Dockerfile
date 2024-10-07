# Use the official Python image
FROM python:3.10

# Set the working directory
WORKDIR /Earls_Discount_System

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8080 for the application to run on
EXPOSE 8080

# Run the Django development server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "Earls_Discount_System.Earls_Discount_System.wsgi:application"]