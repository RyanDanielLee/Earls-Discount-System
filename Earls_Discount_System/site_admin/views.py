from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Cardholder, CardType, Company, Card, WalletSelectionToken
from .utils import send_wallet_selection_email, generate_card_number

def admin_home(request):
    one_month_ago = timezone.now() - timedelta(days=30)
    new_cardholders = Cardholder.objects.filter(issued_date__gte=one_month_ago)
    
    for cardholder in new_cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"
        cardholder.status = "Active" if cardholder.is_active == -1 else "Inactive"

    return render(request, 'admin/home.html', {'new_cardholders': new_cardholders})

# Cardholders
def view_all_users(request):
    return HttpResponse("View All Users Page")

def manage_user_details(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"
    cardholder.status = "Active" if cardholder.is_active == -1 else "Inactive"

    return render(request, 'cardholder/cardholder-details.html',{'cardholder': cardholder})

def manage_card_holders(request):
    cardholders = Cardholder.objects.all()
    for cardholder in cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    return render(request, 'cardholder/cardholder.html', {'cardholders': cardholders})

# EC Card
def issue_card(request):

    if request.method == 'POST':
        # Capture the POST data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        company_id = request.POST.get('company')
        card_type_id = request.POST.get('card_type')
        note = request.POST.get('note')

        company = Company.objects.get(id=company_id)
        cardtype = CardType.objects.get(id=card_type_id)
        
        cardholder = Cardholder.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                company=company,
                card_type=cardtype,
                note=note,
                issued_date=timezone.now(),
                is_active=True
            )
        
        card_number = generate_card_number(company.name)
        
        card = Card.objects.create(
            cardholder=cardholder,
            card_number=card_number,
            issued_date=timezone.now(),
            card_type=cardtype
        )

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
        send_wallet_selection_email(cardholder=cardholder,
            google_wallet_token=google_wallet_token.token,
            apple_wallet_token=apple_wallet_token.token, expires_at=google_wallet_token.expires_at)

        return redirect('manage_card_holders') 

    company = Company.objects.all()
    cardtype = CardType.objects.all()
    
    return render(request, 'eccard/issue-card.html', {'companies': company, 'cardtypes': cardtype})

def revoke_card(request, cardholder_id):
    
    cardholder = Cardholder.objects.get(id=cardholder_id)
    card = Card.objects.filter(cardholder=cardholder).first()
    
    if request.method == 'POST':
 
        if card:
            card.revoked_date = timezone.now()
            card.save()

        cardholder.is_active = False
        cardholder.save()

        return redirect('manage_card_holders') 

    return render(request, 'eccard/revoke-card.html', {
        'cardholder': cardholder,
        'card': card
    })

def edit_card(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)

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
        'companies': company,
        'card_types': cardtype
    })

def delete_cardholder(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    
    # Delete related cards
    cardholder.card_set.all().delete()
    
    # Delete related wallet selection tokens
    WalletSelectionToken.objects.filter(cardholder=cardholder).delete()
    
    # Delete the cardholder
    cardholder.delete()
    
    return redirect('manage_card_holders')

def upload_card_faceplate(request):
    return render(request, 'eccard/upload-faceplate.html')

def view_card_faceplate(request):
    return render(request, 'eccard/view-faceplate.html')

# Reports
def reports_dashboard(request):
    return render(request, 'reports/reports-dashboard.html')

def total_discounts_per_store(request):
    return render(request, 'reports/reports-store.html')

def drilldown_store(request):
    return render(request, 'reports/drilldown-store.html')

def total_discounts_per_employee(request):
    return render(request, 'reports/reports-employee.html')

def drilldown_employee(request):
    return render(request, 'reports/drilldown-employee.html')

def view_sent_email_reports(request):
    return HttpResponse("View Sent Email Reports Page")

# Supports
def manage_user_guides(request):
    return HttpResponse("Manage User Guides Page")

def manage_report_issues(request):
    return HttpResponse("Manage Report Issues Page")