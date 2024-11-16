from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Cardholder, CardType, Company, Card
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test
from .utils import send_wallet_selection_email, generate_card_number

def is_admin(user):
    return user.groups.filter(name='admin').exists()

def is_superadmin(user):
    return user.groups.filter(name='admin').exists() and user.groups.filter(name="superadmin").exists()


@user_passes_test(is_admin, login_url='/unauthorized')
def admin_home(request):
    one_month_ago = timezone.now() - timedelta(days=30)
    new_cardholders = Cardholder.objects.filter(issued_date__gte=one_month_ago)

    for cardholder in new_cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"
        cardholder.status = "Active" if cardholder.is_active == -1 else "Inactive"

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
    cardholder.status = "Active" if cardholder.is_active == -1 else "Inactive"

    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    return render(request, 'cardholder/cardholder-details.html',{'cardholder': cardholder, 'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_admin, login_url='/unauthorized')
def manage_card_holders(request):
    cardholders = Cardholder.objects.all()
    for cardholder in cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    return render(request, 'cardholder/cardholder.html', {'cardholders': cardholders, 'is_superadmin': is_superadmin, 'is_admin': is_admin})


# EC Card
@user_passes_test(is_superadmin, login_url='/unauthorized')
def issue_card(request):

    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    
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

        send_wallet_selection_email(cardholder)

        return redirect('manage_card_holders') 

    company = Company.objects.all()
    cardtype = CardType.objects.all()
    
    return render(request, 'eccard/issue-card.html', {'companies': company, 'cardtypes': cardtype, 'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_superadmin, login_url='/unauthorized')
def revoke_card(request, cardholder_id):

    is_superadmin = request.user.groups.filter(name='superadmin').exists()

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
        'card': card, 'is_superadmin': is_superadmin, 'is_admin': is_admin
    })

@user_passes_test(is_superadmin, login_url='/unauthorized')
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
        'card_types': cardtype,'is_superadmin': is_superadmin, 'is_admin': is_admin
    })


@user_passes_test(is_superadmin, login_url='/unauthorized')
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
