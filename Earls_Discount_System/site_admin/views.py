from datetime import timedelta, datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from .utils import send_wallet_selection_email, generate_card_number
from .models import Cardholder, CardType, Company, Card, WalletSelectionToken, Store
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

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

from .bigquery_helper import fetch_bigquery_data
from django.db import connection
# search
from django.db.models import Q
# pagination
from django.core.paginator import Paginator



def is_admin(user):
    return user.groups.filter(name='admin').exists()

def is_superadmin(user):
    return user.groups.filter(name='admin').exists() and user.groups.filter(name="superadmin").exists()


@user_passes_test(is_admin, login_url='/unauthorized')
def admin_home(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    one_month_ago = timezone.now() - timedelta(days=30)
    new_cardholders = Cardholder.objects.filter(created_date__gte=one_month_ago).order_by('-created_date')

    for cardholder in new_cardholders:
        cardholder.card = Card.objects.filter(cardholder=cardholder).first()
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    if cardholder.card and cardholder.card.issued_date:
        cardholder.card.issued_date = cardholder.card.issued_date.strftime('%Y-%m-%d')

    # Total Discounts by Store
    store_query = """
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
    ORDER BY known_cardholder_discount + unknown_cardholder_discount ASC
    LIMIT 3
    """
    stores = fetch_bigquery_data(store_query)

    store_discounts = [
        {
            "store_name": row["store_name"],
            "total_discount": row["known_cardholder_discount"] + row["unknown_cardholder_discount"],
        }
        for row in stores
    ]

    # Total Discounts by Employee
    cloudsql_query = """
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
    """
    with connection.cursor() as cursor:
        cursor.execute(cloudsql_query)
        cardholder_data = cursor.fetchall()

    cardholders = {
        row[0]: {"cardholder_name": row[1], "card_type": row[2], "total_discount": 0}
        for row in cardholder_data
    }

    bigquery_query = """
    SELECT
        gc.empNum AS cardholder_id,
        SUM(gc.dscTtl) AS total_discount
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    GROUP BY gc.empNum
    """
    bigquery_results = fetch_bigquery_data(bigquery_query)

    for row in bigquery_results:
        cardholder_id = row['cardholder_id']
        if cardholder_id in cardholders:
            cardholders[cardholder_id]['total_discount'] = row['total_discount']

    employee_discounts = sorted(
        [
            {
                "cardholder_name": cardholder["cardholder_name"],
                "total_discount": cardholder["total_discount"],
            }
            for cardholder_id, cardholder in cardholders.items()
        ],
        key=lambda x: x["total_discount"],
        reverse=False  # Sort by ascending order
    )[:3]

    paginator = Paginator(new_cardholders, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/home.html', {'page_obj': page_obj, 'store_discounts': store_discounts,
        'employee_discounts': employee_discounts,  'is_superadmin': is_superadmin, 'is_admin': is_admin})

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
    if card and card.issued_date:
        card.issued_date = card.issued_date.strftime('%Y-%m-%d')
    else:
        card = None 

    # Query BigQuery for transactions related to the cardholder
    bigquery_query = f"""
    SELECT
        gc.clsdBusDt AS business_date,
        sr.store_name AS store,
        gc.chkNum AS check_number,
        gc.dscTtl AS discount_amount
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    JOIN
        `bcit-ec.simphony_api_dataset.store_reference` AS sr
    ON
        gc.locRef = sr.store_id
    WHERE
        gc.empNum = {cardholder_id}
    ORDER BY
        gc.clsdBusDt DESC
    """
    transactions = fetch_bigquery_data(bigquery_query)

    formatted_transactions = []
    for transaction in transactions:
        transaction["business_date"] = (
            transaction["business_date"].strftime("%Y-%m-%d")
            if not isinstance(transaction["business_date"], str)
            else transaction["business_date"]
        )
        formatted_transactions.append(transaction)
    
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'cardholder/cardholder-details.html',{'cardholder': cardholder, 'card': card, 'page_obj': page_obj})

@user_passes_test(is_admin, login_url='/unauthorized')
def manage_card_holders(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    
    cardholders = Cardholder.objects.all().order_by('-created_date')
    for cardholder in cardholders:
        cardholder.name = f"{cardholder.first_name} {cardholder.last_name}"

    paginator = Paginator(cardholders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'cardholder/cardholder.html', {'page_obj': page_obj, 'is_superadmin': is_superadmin, 'is_admin': is_admin})

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
    
    cardholder_query = """
    SELECT COUNT(*) as total_cardholders 
    FROM card_issue.cardholder
    WHERE is_active = 1
    """
    with connection.cursor() as cursor:
        cursor.execute(cardholder_query)
        total_cardholders = cursor.fetchone()[0]

    # Fetch count for each card type
    card_type_query = """
    SELECT
        ct.name AS card_type,
        COUNT(c.id) AS card_count
    FROM
        card_issue.card_type AS ct
    LEFT JOIN
        card_issue.cardholder AS c
    ON
        ct.id = c.card_type_id AND c.is_active = 1
    GROUP BY
        ct.name
    """
    with connection.cursor() as cursor:
        cursor.execute(card_type_query)
        card_type_data = cursor.fetchall()

    card_type_counts = {
        row[0]: row[1] for row in card_type_data
    }

    ec10_count = card_type_counts.get("EC10", 0)
    ec50_count = card_type_counts.get("EC50", 0)
    ec100_count = card_type_counts.get("EC100", 0)


    # total discounts by store
    store_query = """
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
    ORDER BY known_cardholder_discount + unknown_cardholder_discount ASC
    LIMIT 3
    """
    stores = fetch_bigquery_data(store_query)

    store_discounts = [
        {
            "store_name": row["store_name"],
            "known_cardholder_discount": row["known_cardholder_discount"],
            "unknown_cardholder_discount" : row["unknown_cardholder_discount"],
        }
        for row in stores
    ]

    # total discounts by employee
    cloudsql_query = """
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
    """
    with connection.cursor() as cursor:
        cursor.execute(cloudsql_query)
        cardholder_data = cursor.fetchall()

    cardholders = {
        row[0]: {"cardholder_name": row[1], "card_type": row[2], "total_discount": 0, "visit_count": 0}
        for row in cardholder_data
    }

    bigquery_query = """
    SELECT
        gc.empNum AS cardholder_id,
        SUM(gc.dscTtl) AS total_discount,
        COUNT(DISTINCT gc.locRef) AS visit_count
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    GROUP BY gc.empNum
    """
    bigquery_results = fetch_bigquery_data(bigquery_query)

    for row in bigquery_results:
        cardholder_id = row['cardholder_id']
        if cardholder_id in cardholders:
            cardholders[cardholder_id]['total_discount'] = row['total_discount']
            cardholders[cardholder_id]['visit_count'] = row['visit_count']

    employee_discounts = sorted(
        [
            {
                "cardholder_id": cardholder_id, 
                "cardholder_name": cardholder["cardholder_name"],
                "visit_count": cardholder["visit_count"],
                "total_discount": cardholder["total_discount"],
            }
            for cardholder_id, cardholder in cardholders.items()
        ],
        key=lambda x: x["total_discount"],
        reverse=False  # Sort by ascending order
    )[:3]

    # Fetch total discounts for the current month, last month, and the current year
    bigquery_totals_query = """
    SELECT
        SUM(CASE WHEN EXTRACT(MONTH FROM gc.clsdBusDt) = EXTRACT(MONTH FROM CURRENT_DATE()) THEN gc.dscTtl ELSE 0 END) AS this_month_total,
        SUM(CASE WHEN EXTRACT(MONTH FROM gc.clsdBusDt) = EXTRACT(MONTH FROM CURRENT_DATE()) - 1 THEN gc.dscTtl ELSE 0 END) AS last_month_total,
        SUM(CASE WHEN EXTRACT(YEAR FROM gc.clsdBusDt) = EXTRACT(YEAR FROM CURRENT_DATE()) THEN gc.dscTtl ELSE 0 END) AS this_year_total
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    """
    bigquery_totals = fetch_bigquery_data(bigquery_totals_query)[0]

    total_this_month = bigquery_totals["this_month_total"]
    total_last_month = bigquery_totals["last_month_total"]
    total_this_year = bigquery_totals["this_year_total"]

    return render(request, 'reports/reports-dashboard.html', {
        'total_cardholders': total_cardholders,
        'ec10_count': ec10_count,
        'ec50_count': ec50_count,
        'ec100_count': ec100_count,
        'store_discounts':store_discounts,
        'employee_discounts': employee_discounts,
        'total_this_month': total_this_month,
        'total_last_month': total_last_month,
        'total_this_year': total_this_year,
        'is_superadmin': is_superadmin, 
        'is_admin': is_admin
    })

@user_passes_test(is_admin, login_url='/unauthorized')
def total_discounts_per_store(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    stores = Store.objects.all()
    
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
    ORDER BY known_cardholder_discount + unknown_cardholder_discount ASC
    """

    stores = fetch_bigquery_data(query)

    paginator = Paginator(stores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'reports/reports-store.html', {'page_obj': page_obj, 'is_superadmin': is_superadmin, 'is_admin': is_admin})

@user_passes_test(is_admin, login_url='/unauthorized')
def drilldown_store(request, store_name):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()

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
        'is_superadmin': is_superadmin, 
        'is_admin': is_admin
    })


@user_passes_test(is_admin, login_url='/unauthorized')
def total_discounts_per_employee(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    # to get period
    current_date = datetime.now().strftime('%Y-%m-%d')

    bigquery_query_years = """
    SELECT DISTINCT year FROM `bcit-ec.simphony_api_dataset.financial_calendars`
    ORDER BY year ASC
    """
    years = [row['year'] for row in fetch_bigquery_data(bigquery_query_years)]

    default_year_query = f"""
    SELECT year
    FROM `bcit-ec.simphony_api_dataset.financial_calendars`
    WHERE calendar_date = '{current_date}'
    LIMIT 1
    """
    default_year_data = fetch_bigquery_data(default_year_query)
    default_year = default_year_data[0]['year'] if default_year_data else years[-1]

    # Retrieve user-selected values or default year
    selected_year = request.GET.get('year', default_year)
    selected_period = request.GET.get('period')
    selected_week = request.GET.get('week')

    # Query to fetch period and week options for the selected year
    bigquery_query_periods = f"""
    SELECT DISTINCT period FROM `bcit-ec.simphony_api_dataset.financial_calendars`
    WHERE year = {selected_year}
    ORDER BY period ASC
    """
    bigquery_query_weeks = f"""
    SELECT DISTINCT week FROM `bcit-ec.simphony_api_dataset.financial_calendars`
    WHERE year = {selected_year}
    ORDER BY week ASC
    """
    periods = [row['period'] for row in fetch_bigquery_data(bigquery_query_periods)]
    weeks = [row['week'] for row in fetch_bigquery_data(bigquery_query_weeks)]

    # Build the filtering condition
    filters = [f"fc.year = {selected_year}"]
    if selected_period:
        filters.append(f"fc.period = {selected_period}")
    if selected_week:
        filters.append(f"fc.week = {selected_week}")

    # Read data
    cloudsql_query = """
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
    """
    with connection.cursor() as cursor:
        cursor.execute(cloudsql_query)
        cardholder_data = cursor.fetchall()

    # Convert CloudSQL results into a dictionary for easier merging
    cardholders = {
        row[0]: {"cardholder_name": row[1], "card_type": row[2], "total_discount": 0, "visit_count": 0}
        for row in cardholder_data
    }

    # Query to fetch aggregated data from BigQuery
    bigquery_query = f"""
    SELECT
        gc.empNum AS cardholder_id,
        SUM(gc.dscTtl) AS total_discount,
        COUNT(DISTINCT gc.locRef) AS visit_count
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    JOIN
        `bcit-ec.simphony_api_dataset.financial_calendars` AS fc
    ON
        gc.clsdBusDt = fc.calendar_date
    WHERE
        {" AND ".join(filters)}
    GROUP BY
        gc.empNum
    """
    bigquery_results = fetch_bigquery_data(bigquery_query)

    # Merge BigQuery data with CloudSQL data
    for row in bigquery_results:
        cardholder_id = row['cardholder_id']
        if cardholder_id in cardholders:
            cardholders[cardholder_id]['total_discount'] = row['total_discount']
            cardholders[cardholder_id]['visit_count'] = row['visit_count']

    # Prepare data for pagination
    employee_list = sorted(
        [
            {
                "cardholder_id": cardholder_id, 
                "cardholder_name": cardholder["cardholder_name"],
                "visit_count": cardholder["visit_count"],
                "total_discount": cardholder["total_discount"],
                "card_type": cardholder["card_type"],
            }
            for cardholder_id, cardholder in cardholders.items()
        ],
        key=lambda x: x["total_discount"],
        reverse=False  # Sort by ascending order
    )

    paginator = Paginator(employee_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/reports-employee.html', {
        'page_obj': page_obj,
        'years': years,
        'periods': periods,
        'weeks': weeks,
        'selected_year': int(selected_year),
        'selected_period': int(selected_period) if selected_period else '',
        'selected_week': int(selected_week) if selected_week else '',
        'is_superadmin': is_superadmin,
        'is_admin': is_admin
    })

@user_passes_test(is_admin, login_url='/unauthorized')
def drilldown_employee(request, cardholder_id):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()

    selected_year = request.GET.get('year')
    selected_period = request.GET.get('period')
    selected_week = request.GET.get('week')

    cloudsql_query = """
    SELECT
        ch.first_name,
        ch.last_name,
        ct.name AS card_type,
        c.card_number,
        c.issued_date
    FROM
        cardholder AS ch
    LEFT JOIN
        card_type AS ct
    ON
        ch.card_type_id = ct.id
    LEFT JOIN
        card AS c
    ON
        ch.id = c.cardholder_id
    WHERE
        ch.id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(cloudsql_query, [cardholder_id])
        cardholder_details = cursor.fetchone()

    # Handle case where cardholder is not found
    if not cardholder_details:
        return render(request, 'error.html')

    cardholder_name = f"{cardholder_details[0]} {cardholder_details[1]}"
    card_type = cardholder_details[2] or "N/A"
    card_number = cardholder_details[3] or "N/A"
    issued_date = cardholder_details[4].strftime("%Y-%m-%d") if cardholder_details[4] else "N/A"

    # Query BigQuery for transactions related to the cardholder
    filters = []
    if selected_year:
        filters.append(f"EXTRACT(YEAR FROM gc.clsdBusDt) = {selected_year}")
    if selected_period:
        filters.append(f"fc.period = {selected_period}")
    if selected_week:
        filters.append(f"fc.week = {selected_week}")

    # Query BigQuery for transactions related to the cardholder
    bigquery_query = f"""
    SELECT
        gc.clsdBusDt AS business_date,
        sr.store_name AS store,
        gc.chkNum AS check_number,
        gc.dscTtl AS discount_amount
    FROM
        `bcit-ec.simphony_api_dataset.guest_checks` AS gc
    JOIN
        `bcit-ec.simphony_api_dataset.store_reference` AS sr
    ON
        gc.locRef = sr.store_id
    WHERE
        gc.empNum = {cardholder_id}
    ORDER BY
        gc.clsdBusDt DESC
    """
    transactions = fetch_bigquery_data(bigquery_query)

    formatted_transactions = []
    for transaction in transactions:
        transaction["business_date"] = (
            transaction["business_date"].strftime("%Y-%m-%d")
            if not isinstance(transaction["business_date"], str)
            else transaction["business_date"]
        )
        formatted_transactions.append(transaction)

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/drilldown-employee.html', {
        'cardholder_name': cardholder_name,
        'card_type': card_type,
        'card_number': card_number,
        'issued_date': issued_date,
        'page_obj': page_obj,
        'selected_year': selected_year,
        'selected_period': selected_period,
        'selected_week': selected_week,
        'is_superadmin': is_superadmin,
        'is_admin': is_admin
    })



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
