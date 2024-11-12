from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import WalletSelectionToken, Card, DigitalWallet
from django.conf import settings

def send_wallet_selection_email(cardholder):
    # Generate a new token and expiration date
    token = WalletSelectionToken.objects.create(
        cardholder=cardholder,
        expires_at=timezone.now() + timedelta(hours=1)  # 1-hour expiration
    )

    # Prepare context for email template
    context = {
        'first_name': cardholder.first_name,
        'token': token.token,
        'expiration': token.expires_at,
    }

    # Render the HTML template with context
    html_content = render_to_string('eccard/wallet_selection_email.html', context)
    text_content = strip_tags(html_content)

    # Send the email
    send_mail(
        subject='Digital ECcard is ready for you',
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