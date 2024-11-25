from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Q

from .models import (
    Cardholder,
    CardType,
    Company,
    Card,
    WalletSelectionToken
)
from .utils import (
    generate_card_number,
    issue_card_to_google_wallet,
    revoke_google_wallet_card,
    send_wallet_selection_email
)

# search
from django.db.models import Q

def is_admin(user):
    return user.groups.filter(name='admin').exists()

def is_superadmin(user):
    return user.groups.filter(name='admin').exists() and user.groups.filter(name="superadmin").exists()


@user_passes_test(is_admin, login_url='/unauthorized')
def admin_home(request):
    one_month_ago = timezone.now() - timedelta(days=30)
    new_cardholders = Cardholder.objects.filter(created_date__gte=one_month_ago).order_by('-created_date')

    for cardholder in new_cardholders:
        cardholder.card = Card.objects.filter(cardholder=cardholder).first()
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    return render(request, 'admin/home.html', {'new_cardholders': new_cardholders, 'is_superadmin': is_superadmin, 'is_admin': is_admin})


# Cardholders
@user_passes_test(is_admin, login_url='/unauthorized')
def view_all_users(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'cardholder/view_all_users.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def manage_user_details(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"
    cardholder.status = "Active" if cardholder.is_active == True else "Inactive"

    card = Card.objects.filter(cardholder=cardholder).first()

    return render(request, 'cardholder/cardholder-details.html',{'cardholder': cardholder, 'card': card})

@user_passes_test(is_admin, login_url='/unauthorized')
def manage_card_holders(request):
    cardholders = Cardholder.objects.all()
    for cardholder in cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    return render(request, 'cardholder/cardholder.html', {'cardholders': cardholders, 'is_superadmin': is_superadmin, 'is_admin': is_admin})


def search_cardholders(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'name')  # Default to search by name

    if filter_by == 'name':
        cardholders = Cardholder.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
    elif filter_by == 'email':
        cardholders = Cardholder.objects.filter(email__icontains=query)
    elif filter_by == 'id':
        cardholders = Cardholder.objects.filter(id=query)
    else:
        cardholders = Cardholder.objects.none()

    return render(request, 'cardholder/search_results.html', {'cardholders': cardholders, 'query': query, 'filter_by': filter_by})


@user_passes_test(is_superadmin, login_url='/unauthorized')
def issue_card(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    
    if request.method == 'POST':
        try:
            # Capture the POST data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            company_id = request.POST.get('company')
            card_type_id = request.POST.get('card_type')
            note = request.POST.get('note')

            # Fetch related objects from the database
            company = Company.objects.get(id=company_id)
            cardtype = CardType.objects.get(id=card_type_id)

            # Create a new Cardholder
            cardholder = Cardholder.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                company=company,
                card_type=cardtype,
                note=note,
                created_date=timezone.now(),
                is_active=True
            )

            # Generate card number and create Card instance
            card_number = generate_card_number(company.name)
            card = Card.objects.create(
                cardholder=cardholder,
                card_number=card_number,
                issued_date=timezone.now(),
            )

            cardholder.card = card
            cardholder.save()

            # Call the separate function to issue the card to Google Wallet
            wallet_response = issue_card_to_google_wallet(
                company_name=company.name,
                first_name=first_name,
                last_name=last_name,
                email=email,
                card_type_name=cardtype.name,
                note=note
            )

            if wallet_response['status'] == 'success':
                # Store the wallet ID in the card
                card.wallet_id = wallet_response.get('google_wallet_id', None)  # Use 'google_wallet_id' from the response
                card.save()

                # Generate wallet selection tokens
                google_wallet_token = WalletSelectionToken.objects.create(
                    cardholder=cardholder,
                    expires_at=timezone.now() + timezone.timedelta(hours=1)
                )
                apple_wallet_token = WalletSelectionToken.objects.create(
                    cardholder=cardholder,
                    expires_at=timezone.now() + timezone.timedelta(hours=1)
                )
                
                # Send email with wallet selection links
                send_wallet_selection_email(
                    cardholder=cardholder,
                    google_wallet_token=google_wallet_token.token,
                    apple_wallet_token=apple_wallet_token.token,
                    expires_at=google_wallet_token.expires_at
                )

                return redirect('manage_card_holders')

            else:
                # Handle error response
                error_message = wallet_response.get('message', 'Unknown error occurred.')
                print(f"Failed to issue Google Wallet card: {error_message}")
                messages.error(request, f"Failed to issue Google Wallet card: {error_message}")

        except Exception as e:
            print(f"Error issuing card: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")

        # Redirect back to the form in case of any error
        return redirect('issue_card')

    # Get data for rendering the form
    companies = Company.objects.all()
    cardtypes = CardType.objects.all()

    return render(
        request,
        'eccard/issue-card.html',
        {
            'companies': companies,
            'cardtypes': cardtypes,
            'is_superadmin': is_superadmin
        }
    )


@user_passes_test(is_superadmin, login_url='/unauthorized')
def revoke_card(request, cardholder_id):

    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    cardholder = Cardholder.objects.get(id=cardholder_id)
    card = Card.objects.filter(cardholder=cardholder).first()
    
    if request.method == 'POST':
        if card:
            card.card_number = None
            card.issued_date = None
            card.revoked_date = timezone.now()
            card.save()

        cardholder.is_active = False
        cardholder.save()

        
        revoke_google_wallet_card(f"3388000000022791702.{cardholder.first_name}.{cardholder.last_name}")
        return redirect('manage_user_details', cardholder_id=cardholder.id) 

    return render(request, 'eccard/revoke-card.html', {
        'cardholder': cardholder,
        'card': card, 'is_superadmin': is_superadmin, 'is_admin': is_admin
    })

@user_passes_test(is_superadmin, login_url='/unauthorized')
def edit_card(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    card = Card.objects.filter(cardholder=cardholder).first()

    if request.method == 'POST':
        cardholder.first_name = request.POST.get('first_name')
        cardholder.last_name = request.POST.get('last_name')
        cardholder.email = request.POST.get('email')
        cardholder.note = request.POST.get('note')
        company_id = request.POST.get('company')
        card_type_id = request.POST.get('card_type')


        if company_id:
            cardholder.company = Company.objects.get(id=company_id)


        if card_type_id:
            cardholder.card_type = CardType.objects.get(id=card_type_id)

        cardholder.save()
        return redirect('manage_user_details', cardholder_id=cardholder.id) 
    
    company = Company.objects.all()
    cardtype = CardType.objects.all()

    return render(request, 'eccard/edit-card.html', {
        'cardholder': cardholder,
        'card': card, 
        'companies': company,
        'card_types': cardtype,'is_superadmin': is_superadmin, 'is_admin': is_admin
    })

def delete_cardholder(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    
    # Delete related cards
    cardholder.cards.all().delete()
    
    # Delete related wallet selection tokens
    WalletSelectionToken.objects.filter(cardholder=cardholder).delete()
    
    # Delete the cardholder
    cardholder.delete()
    
    return redirect('manage_card_holders')

def reissue_card(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    card = Card.objects.filter(cardholder=cardholder).first()

    if cardholder.is_active:
        return render(request, 'error.html', {'message': 'Cardholder already has an active card.'})

    if card:
        card.card_number = generate_card_number(cardholder.company.name)
        card.issued_date = timezone.now()
        card.revoked_date = None  # Reset revoked date
        card.save()

    cardholder.is_active = True
    cardholder.save()

    # Generate new wallet selection tokens again
    google_wallet_token = WalletSelectionToken.objects.create(
        cardholder=cardholder,
        expires_at=timezone.now() + timezone.timedelta(hours=1)
    )
    apple_wallet_token = WalletSelectionToken.objects.create(
        cardholder=cardholder,
        expires_at=timezone.now() + timezone.timedelta(hours=1)
    )

    # Send a new wallet selection email again
    send_wallet_selection_email(
        cardholder=cardholder,
        google_wallet_token=google_wallet_token.token,
        apple_wallet_token=apple_wallet_token.token,
        expires_at=google_wallet_token.expires_at
    )

    # Redirect to the cardholder's detail page
    return redirect('manage_user_details', cardholder_id=cardholder_id)

def upload_card_faceplate(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'eccard/upload-faceplate.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_superadmin, login_url='/unauthorized')
def view_card_faceplate(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'eccard/view-faceplate.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


# Reports
@user_passes_test(is_admin, login_url='/unauthorized')
def reports_dashboard(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'reports/reports-dashboard.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def total_discounts_per_store(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'reports/reports-store.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def drilldown_store(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'reports/drilldown-store.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def total_discounts_per_employee(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'reports/reports-employee.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def drilldown_employee(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'reports/drilldown-employee.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def view_sent_email_reports(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'reports/view-sent-email-reports.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


# Supports
@user_passes_test(is_admin, login_url='/unauthorized')
def manage_user_guides(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'supports/manage_user_guides.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def manage_report_issues(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'supports/manage_report_issues.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})
