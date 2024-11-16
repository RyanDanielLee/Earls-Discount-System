# Earls-Discount-System

## Running the Project

1. Clone the repository and navigate to it
2. Set up a virtual environment  
   a. For **Windows**: In terminal, run `python -m venv env` and `.\env\Scripts\Activate`
   b. For **macOS/Linux**: In terminal, run `python3 -m venv env` and `source venv/bin/activate`
3. Install required packages using `pip install -r requirements.txt`
4. Change directory to "Earls_Discount_System"
5. Log in to Google Cloud `gcloud auth application-default login`
   <br>(If you have MySQL installed locally, stop the MySQL service to avoid conflicts)
6. Run Cloud SQL Proxy where `cloud-sql-proxy.exe` is located before running the application
   <br>`./cloud-sql-proxy bcit-ec:us-west1:card-issuer`
   <br>(Keep the terminal open while the Cloud SQL Proxy is running)
7. Change directory to Earls_Discount_System
8. Apply any migrations, `python manage.py migrate`
9. Start the application using `python manage.py runserver`
10. View the project at http://127.0.0.1:8000/

## For Developers

1. Ensure you have a dedicated folder for the project, and change directory into said folder
2. In terminal, run the command `git clone https://github.com/RyanDanielLee/Earls-Discount-System.git`

## Connecting to Database

1. Whitelist IP on CloudSQL under the **card-issuer** interface in the **card-issue** database
2. Change directory to "Earls_Discount_System\Earls_Discount_System\
3. Start the database connection using `python manage.py migrate`
