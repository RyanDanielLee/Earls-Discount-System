import os
import requests 
import json
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from google.oauth2 import service_account
from google.auth.transport.requests import Request
# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from .models import WalletSelectionToken, Card, DigitalWallet, Cardholder

# Path to your service account key file
SERVICE_ACCOUNT_FILE = "C:\\Users\\josh_\\Desktop\\bcit-ec-9f137ee9c6ae.json"

def send_wallet_selection_email(cardholder, google_wallet_token, apple_wallet_token, expires_at):

    # Prepare context for email template
    context = {
        'first_name': cardholder.first_name,
         'google_wallet_link': google_wallet_token,
        'apple_wallet_link': f"https://your-domain.com/wallet/apple?token={apple_wallet_token}",
        'expiration': expires_at, 
    }

    # Render the HTML template with context
    html_content = render_to_string('eccard/wallet_selection_email.html', context)

    # # Send the email
    # send_mail(
    #     subject='Your Digital EC Card is Ready!',
    #     message=text_content,
    #     from_email='devteam@earls.ca',
    #     recipient_list=[cardholder.email],
    #     html_message=html_content,
    # )

    message = Mail(
        from_email='devteam@earls.ca',
        to_emails=cardholder.email,
        subject='Your Digital EC Card is Ready!',
        html_content=render_to_string('eccard/wallet_selection_email.html', context) )
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)

    except Exception as e:
        print(str(e))

def generate_card_number(company_name):
    # Define the card number ranges for each company
    company_ranges = {
        'Earls': [(1, 400), (1000, 9999)],  
        'Joey': [(401, 999)]                
    }

    if company_name in company_ranges:
        
        for range_start, range_end in company_ranges[company_name]:
            # Get the highest existing card number in this range
            latest_card = Card.objects.filter(
                cardholder__company__name=company_name,
                card_number__gte=range_start,
                card_number__lt=range_end
            ).order_by('-card_number').first()

            if latest_card is not None:
                next_number = latest_card.card_number + 1
                if next_number <= range_end:
                    return next_number
            else:
                # If no card in range, start from the range's beginning
                return range_start


def create_digital_wallet(card, wallet_type):
    DigitalWallet.objects.create(card=card, wallet_type=wallet_type)

def get_google_wallet_token():
    # Define the required scopes
    SCOPES = ['https://www.googleapis.com/auth/wallet_object.issuer']
    
    # Load the credentials and create a request
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Refresh the credentials to get the access token
    auth_request = Request()
    credentials.refresh(auth_request)
    
    return credentials.token  # Return only the access token

def create_google_wallet_jwt(issuer_id, service_account_file, card_data, audience="google"):
    """
    Generate a signed JWT containing card details for Google Wallet.

    Args:
        issuer_id (str): Your Google Wallet issuer ID.
        service_account_file (str): Path to your service account JSON file.
        card_data (dict): The card data to embed in the JWT.
        audience (str): The audience for the JWT (default: "google").

    Returns:
        str: A signed JWT ready to be sent to Google Wallet.
    """
    try:
        # Load the service account key JSON
        with open(service_account_file, "r") as file:
            service_account_info = json.load(file)
        
        # Extract the private key
        private_key = service_account_info["private_key"]

        # Define the JWT payload
        now = datetime.now(timezone.utc)
        payload = {
            "iss": service_account_info["client_email"],  # Issuer ID
            "aud": audience,   # Audience (usually "google")
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "typ": "savetowallet",  # Type of JWT for Google Wallet
            "payload": {
                "genericObjects": [card_data]  # Embed the card data in the payload
            }
        }
        # Sign the JWT with the private key
        signed_jwt = jwt.encode(payload, private_key, algorithm="RS256")

        return signed_jwt
    except Exception as e:
        print(f"Error creating signed JWT: {str(e)}")
        return None


def issue_card_to_google_wallet(company_name, first_name, last_name, email, card_type_name, note):
    try:
        issuer_id = "3388000000022791702"  # Your actual issuer ID

        # Define the card details for the Generic Object
        card_data = {
            "id": f"{issuer_id}.{first_name}.{last_name}",  # Unique identifier for this card object
            "classId": f"{issuer_id}.{card_type_name}",  # Match the working classId
            "state": "active",  # Use lowercase "active" as per your working example
            "accountId": email,
            "accountName": first_name,
            "issuerName": company_name,
            "textModulesData": [
                #{"id": "employee_no", "header": "Employee No", "body": "1061"},
                #{"id": "partner_since", "header": "Partner Since", "body": "2019"},
                {"id": "company", "header": "Company", "body": company_name},
                {"id": "note", "header": "Note", "body": note},
                {"id": "survey_link", "header": "Survey", "body": "Please provide your feedback at: https://earls.ca/myexperience/"}
            ],
            "hexBackgroundColor": "#082f3e",
            "logo": {
                "sourceUri": {
                    "uri": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLC_RMqXRRPwxO18b4Xhq2P4iaKAD9lObR5A&s"
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": "Company Logo"
                    }
                }
            },
            "barcode": {
                "type": "QR_CODE",
                "value": f'Discount: {card_type_name[2:]}%',
                "alternateText": "Scan for Discount"
            },
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": "Discount Card"
                }
            },
            "subheader": {
                "defaultValue": {
                    "language": "en-US",
                    "value": "Employee"
                }
            },
            "header": {
                "defaultValue": {
                    "language": "en-US",
                    "value": f'{first_name} {last_name}'
                }
            },
        }

        # Generate a signed JWT containing the card details
        signed_jwt = create_google_wallet_jwt(issuer_id, SERVICE_ACCOUNT_FILE, card_data)

        if not signed_jwt:
            print("Failed to generate signed JWT.")
            return {'status': 'error', 'message': 'JWT creation failed.'}

        # Generate the Google Wallet Save link
        google_wallet_link = f"https://pay.google.com/gp/v/save/{signed_jwt}"

        # Debug: Ensure the link is correct and testable
        print(card_data)
        print(f"Google Wallet Link: {google_wallet_link}")

        return {'status': 'success', 'google_wallet_link': google_wallet_link, 'signed_jwt': signed_jwt}
    except Exception as e:
        print(f"Error issuing card: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def revoke_google_wallet_card(object_id):
    """
    Revoke a Google Wallet card by setting its state to 'inactive'.

    Args:
        object_id (str): The unique ID of the card to revoke (e.g., "issuer_id.card_id").

    Returns:
        dict: The API response indicating success or failure.
    """
    try:
        # Authenticate using the service account file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/wallet_object.issuer"]
        )
        authed_session = Request()
        credentials.refresh(authed_session)
        access_token = credentials.token

        # Define the PATCH endpoint and payload
        url = f"https://walletobjects.googleapis.com/walletobjects/v1/genericObject/{object_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"state": "inactive"}

        # Make the PATCH request
        response = requests.patch(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            print(f"Successfully revoked card: {object_id}")
            return {"status": "success", "response": response.json()}
        else:
            print(f"Failed to revoke card: {response.status_code}, {response.text}")
            return {"status": "error", "response": response.json()}

    except Exception as e:
        print(f"Error revoking card: {str(e)}")
        return {"status": "error", "message": str(e)}
