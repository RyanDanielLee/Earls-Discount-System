from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, datetime
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import WalletSelectionToken, Card, DigitalWallet, Cardholder
from django.conf import settings
from dotenv import load_dotenv
import os

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

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


def format_date(date_input):
    if isinstance(date_input, datetime):
        return date_input.strftime("%Y-%m-%d")
    elif isinstance(date_input, str):
        
        date_object = datetime.strptime(date_input, "%Y-%m-%d") 
        return date_object.strftime("%Y-%m-%d")
    return date_input  