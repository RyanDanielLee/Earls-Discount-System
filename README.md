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
   <br>To download [cloud sql proxy](https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.0/cloud-sql-proxy.x64.exe) and Rename the file to cloud-sql-proxy.exe
7. Change directory to Earls_Discount_System
8. Apply any migrations, `python manage.py migrate`
9. Start the application using `python manage.py runserver`
10. View the project at http://127.0.0.1:8000/

## For Developers

1. Ensure you have a dedicated folder for the project, and change directory into said folder
2. In terminal, run the command `git clone https://github.com/RyanDanielLee/Earls-Discount-System.git`

## Local Development Setup

1. To ensure you have the right keys, please head over the console https://console.cloud.google.com/iamadmin/serviceaccounts/details/102373071141954327383/keys?cloudshell=true&hl=en&project=bcit-ec
2. Create a new key pair and download it(JSON)
3. Add this JSON file to your directory in Earls_Discount_System/site_admin/utils.py
4. Change the service account to match the directory of the JSON


## Styling Guide

Please refer to this figma for design reference

https://www.figma.com/design/D7cFY2SOTXWoHZXWAz21jB/EarlsIT---UI%2FUX-Design?node-id=5-8967&t=sWIP9bza2hAXp22q-1

# Styling Conventions Documentation

## Colors and Variables
- **Color Variables:**
  - `var(--font-color)`: Use for all font colors.
  - `var(--bg-variant)`: Use for background variants.
  - `var(--primary-color)`: Use as the main primary color.
  - `var(--primary-light)`: Use for lighter primary shades.
  - `var(--light-color)`: Use for other light colors.

## Units of Measure
- **Rem over Px:**
  - Use `rem` instead of `px` for padding, gaps, and margins to ensure scalability and better accessibility.

## Naming Conventions
- **CSS Naming:**
  - Use lowercase letters followed by a hyphen (`-`).
  - For example: `.eccard-issue`, `.primary-button`.

## Layout and Spacing
- **Flexbox and Grid:**
  - Prefer `flexbox` for laying out.
  - Use `gap` property for spacing between elements in flexbox or grid containers.

## Font and Text
- **Font Sizes:**
  - Use `em` or `rem` units for font sizes to ensure they are scalable.
- **Font Weight:**
  - Use numeric font-weight values (e.g., `font-weight: 400`).

## Comments and Documentation
- **Commenting:**
  - Use comments to explain complex or non-intuitive styles.
  - For example: `/* Main navigation styles */`.


## Connecting to Database

1. Whitelist IP on CloudSQL under the **card-issuer** interface in the **card-issue** database
2. Change directory to "Earls_Discount_System\Earls_Discount_System\
3. Start the database connection using `python manage.py migrate`
