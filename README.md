# Earls-Discount-System

## Running the Project

1. Clone the repository and navigate to it
2. Set up a virtual environment  
   a. For **Windows**: In terminal, run `python -m venv env` and `.\env\Scripts\Activate`  
   b. For **macOS/Linux**: In terminal, run `python3 -m venv env` and `source venv/bin/activate`
3. Install required packages using `pip install -r requirements.txt`
4. Change directory to "Earls_Discount_System"
5. Start the application using `python manage.py runserver`
6. View the project at http://127.0.0.1:8000/

## For Developers

1. Ensure you have a dedicated folder for the project, and change directory into said folder
2. In terminal, run the command `git clone https://github.com/RyanDanielLee/Earls-Discount-System.git`

## Connect to Cloud SQL Instance Using Cloud SQL Proxy

1. Log in to Google Cloud `gcloud auth application-default login`
2. If you have MySQL installed locally, stop the MySQL service to avoid conflicts
3. Run Cloud SQL Proxy where `cloud_sql_proxy.exe` is located before running the application `./cloud-sql-proxy bcit-ec:us-west1:card-issuer`
4. Keep the terminal open while the Cloud SQL Proxy is running
