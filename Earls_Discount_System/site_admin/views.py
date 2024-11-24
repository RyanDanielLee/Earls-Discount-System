from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Cardholder, CardType, Company, Card, WalletSelectionToken, Store
from .utils import send_wallet_selection_email, generate_card_number, format_date
from .bigquery_helper import fetch_bigquery_data
from django.db import connection
# search
from django.db.models import Q
# pagination
from django.core.paginator import Paginator



def admin_home(request):
    one_month_ago = timezone.now() - timedelta(days=30)
    new_cardholders = Cardholder.objects.filter(created_date__gte=one_month_ago).order_by('-created_date')

    for cardholder in new_cardholders:
        cardholder.card = Card.objects.filter(cardholder=cardholder).first()
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    paginator = Paginator(new_cardholders, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/home.html', {'page_obj': page_obj})

# Cardholders
def view_all_users(request):
    return HttpResponse("View All Users Page")

def manage_user_details(request, cardholder_id):
    cardholder = Cardholder.objects.get(id=cardholder_id)
    cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"
    cardholder.status = "Active" if cardholder.is_active == True else "Inactive"

    card = Card.objects.filter(cardholder=cardholder).first()

    return render(request, 'cardholder/cardholder-details.html',{'cardholder': cardholder, 'card': card})

def manage_card_holders(request):
    cardholders = Cardholder.objects.all().order_by('-created_date')
    for cardholder in cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    paginator = Paginator(cardholders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'cardholder/cardholder.html', {'page_obj': page_obj})

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
                created_date=timezone.now(),
                is_active=True
            )
        
        card_number = generate_card_number(company.name)
        
        card = Card.objects.create(
            cardholder=cardholder,
            card_number=card_number,
            issued_date=timezone.now(),
        )

        cardholder.card = card
        cardholder.save()

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
            card.card_number = None
            card.issued_date = None
            card.revoked_date = timezone.now()
            card.save()

        cardholder.is_active = False
        cardholder.save()

        return redirect('manage_user_details', cardholder_id=cardholder.id) 

    return render(request, 'eccard/revoke-card.html', {
        'cardholder': cardholder,
        'card': card
    })

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
        'card_types': cardtype
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
    return render(request, 'eccard/upload-faceplate.html')

def view_card_faceplate(request):
    return render(request, 'eccard/view-faceplate.html')

# Reports
def reports_dashboard(request):
    return render(request, 'reports/reports-dashboard.html')

def total_discounts_per_store(request):
    query = """
    SELECT
        sr.store_name,
        SUM(CASE WHEN gc.chkName IS NOT NULL THEN gc.dscTtl ELSE 0 END) AS known_cardholder_discount,
        SUM(CASE WHEN gc.chkName IS NULL THEN gc.dscTtl ELSE 0 END) AS unknown_cardholder_discount
    FROM
        `bcit-ec.simphony_api_dataset.store_reference` AS sr
    JOIN
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    ON
        sr.store_id = gc.locRef
    GROUP BY sr.store_name
    """

    stores = fetch_bigquery_data(query)

    paginator = Paginator(stores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/reports-store.html', {'page_obj': page_obj})

def drilldown_store(request, store_name):

    show_known = request.GET.get('show_known', None)
    show_unknown = request.GET.get('show_unknown', None) 

    if show_known is None and show_unknown is None:
        show_known = True
        show_unknown = False
    else:
        show_known = show_known == 'true'
        show_unknown = show_unknown == 'true'

    bigquery_query = f"""
    SELECT
        gc.clsdBusDt AS business_date,
        gc.empNum AS cardholder_id,
        gc.chkName AS check_name,
        gc.dscTtl AS discount_amount,
        gc.tipTotal AS tip_amount
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    JOIN
        `bcit-ec.simphony_api_dataset.store_reference` AS sr
    ON
        sr.store_id = gc.locRef
    WHERE
        sr.store_name = "{store_name}"
    ORDER BY business_date DESC
    """
    bigquery_results = fetch_bigquery_data(bigquery_query)

    cardholder_ids = [row['cardholder_id'] for row in bigquery_results if row['cardholder_id']]

    # Query CloudSQL for cardholder details and card types
    placeholders = ",".join(["%s"] * len(cardholder_ids))
    cloudsql_query = f"""
    SELECT
        ch.id AS cardholder_id,
        CONCAT(ch.first_name, ' ', ch.last_name) AS cardholder_name,
        ct.name AS card_type
    FROM
        cardholder AS ch
    LEFT JOIN
        card_type AS ct
    ON
        ch.card_type_id = ct.id
    WHERE
        ch.id IN ({placeholders})
    """

    with connection.cursor() as cursor:
        cursor.execute(cloudsql_query, cardholder_ids)
        cloudsql_results = cursor.fetchall()

    # Convert CloudSQL results to a dictionary
    cardholder_details = {
        row[0]: {"cardholder_name": row[1], "card_type": row[2]} for row in cloudsql_results
    }

    # Combine BigQuery results with CloudSQL details
    transactions = []
    for row in bigquery_results:
        cardholder_detail = cardholder_details.get(row['cardholder_id'], {})
        known_cardholder = row['check_name'] is not None  # Determine if it's a known cardholder
        if (known_cardholder and show_known) or (not known_cardholder and show_unknown):
            transactions.append({
                "business_date": row['business_date'] if isinstance(row['business_date'], str) else row['business_date'].strftime("%Y-%m-%d"),
                "cardholder_name": cardholder_detail.get("cardholder_name", "Noname"),
                "check_name": row['check_name'],
                "card_type": cardholder_detail.get("card_type", "-"),
                "discount_amount": row['discount_amount'],
                "tip_amount": row['tip_amount'],
            })


    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/drilldown-store.html', {
        'store_name': store_name,
        'page_obj': page_obj,
        'show_known': show_known,
        'show_unknown': show_unknown,
    })

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