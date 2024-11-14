from django.shortcuts import render
from django.http import HttpResponse
from .models import Cardholder
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test


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

    return render(request, 'cardholder/cardholder-details.html',
                  {'cardholder': cardholder, 'is_superadmin': is_superadmin, 'is_admin': is_admin})


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
    return render(request, 'eccard/issue-card.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_superadmin, login_url='/unauthorized')
def revoke_card(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'eccard/revoke-card.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


@user_passes_test(is_superadmin, login_url='/unauthorized')
def edit_card(request):
    is_superadmin = request.user.groups.filter(name='superadmin').exists()
    return render(request, 'eccard/edit-card.html', {'is_superadmin': is_superadmin, 'is_admin': is_admin})


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
