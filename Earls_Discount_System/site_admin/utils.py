import os
import json
import requests 
import requests
import json
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import WalletSelectionToken, Card, DigitalWallet, Cardholder
from django.conf import settings
from django.core.mail import send_mail
from django.conf import settings
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from django.http import JsonResponse



def send_wallet_selection_email(cardholder, google_wallet_token, apple_wallet_token, expires_at):

    # Prepare context for email template
    context = {
        'first_name': cardholder.first_name,
         'google_wallet_link': f"https://your-domain.com/wallet/google?token={google_wallet_token}",
        'apple_wallet_link': f"https://your-domain.com/wallet/apple?token={apple_wallet_token}",
        'expiration': expires_at, 
    }

    # Render the HTML template with context
    html_content = render_to_string('eccard/wallet_selection_email.html', context)
    text_content = strip_tags(html_content)

    # Send the email
    send_mail(
        subject='Your Digital EC Card is Ready!',
        message=text_content,
        from_email='studwing@hotmail.com',
        recipient_list=[cardholder.email],
        html_message=html_content,
    )

   
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
    # Path to your service account key file
    SERVICE_ACCOUNT_FILE = "C:\\Users\\josh_\\Desktop\\bcit-ec-9f137ee9c6ae.json"
    
    # Define the required scopes
    SCOPES = ['https://www.googleapis.com/auth/wallet_object.issuer']
    
    # Load the credentials and create a request
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Refresh the credentials to get the access token
    auth_request = Request()
    credentials.refresh(auth_request)
    
    return credentials.token  # Return only the access token

def issue_card_to_google_wallet(company_name, first_name, email, card_type_name, note):
    try:
        # Authenticate and get access token for Google Wallet API
        access_token = get_google_wallet_token()

        # Define the API URL for issuing a generic object
        url = "https://walletobjects.googleapis.com/walletobjects/v1/genericObject"

        # Define the classId
        issuer_id = "3388000000022791702"  # Your actual issuer ID
        class_id = "EC_10"  # Match the working classId
        formatted_class_id = f"{issuer_id}.{class_id}"

        # Define the card details for the Generic Object
        card_data = {
            "id": f"{issuer_id}.{first_name}.generic-card",  # Unique identifier for this card object
            "classId": formatted_class_id,
            "state": "active",  # Use lowercase "active" as per your working example
            "accountId": email,
            "accountName": "John Doe",
            "issuerName": company_name,
            "textModulesData": [
                {"id": "employee_no", "header": "Employee No", "body": "1061"},
                {"id": "discount%", "header": "Discount %", "body": "50"},
                {"id": "partner_since", "header": "Partner Since", "body": "2019"}
            ],
            "hexBackgroundColor": "#082f3e",
            "logo": {
                "sourceUri": {
                    "uri": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLC_RMqXRRPwxO18b4Xhq2P4iaKAD9lObR5A&s"
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": "Earls Corporate Logo"
                    }
                }
            },
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": card_type_name
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
                    "value": email
                }
            },
            "barcode": {
                "type": "QR_CODE",
                "value": "1234567890",
                "alternateText": "Scan for Discount"
            },
            "heroImage": {
                "sourceUri": {
                    "uri": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLC_RMqXRRPwxO18b4Xhq2P4iaKAD9lObR5A&s"
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": "Earls Hero Image"
                    }
                }
            }
        }

        # Debug logs
        print("Request Data:", json.dumps(card_data, indent=2))

        # Set the headers for authorization
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Make the POST request to issue the card
        response = requests.post(url, headers=headers, json=card_data)

        # Check if the request was successful
        if response.status_code == 200:
            card_response = response.json()
            wallet_id = card_response.get('id')
            print(f"Card Issued with ID: {wallet_id}")

            # Generate the Google Wallet link
            google_wallet_link = f"https://pay.google.com/gp/v/save/{wallet_id}"
            print(f"Google Wallet Link: {google_wallet_link}")

            return {'status': 'success', 'wallet_id': wallet_id, 'google_wallet_link': google_wallet_link}
        else:
            print(f"Error response received: {response.status_code} - {response.text}")
            return {'status': 'error', 'message': response.text}

    except Exception as e:
        print(f"Error issuing card: {str(e)}")
        return {'status': 'error', 'message': str(e)}

