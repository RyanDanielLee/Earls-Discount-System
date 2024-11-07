from django.shortcuts import render
from django.http import HttpResponse
from .models import CardsEmployee
from django.utils import timezone
from datetime import timedelta

def admin_home(request):
    one_month_ago = timezone.now() - timedelta(days=30)
    new_cardholders = CardsEmployee.objects.filter(issue_date__gte=one_month_ago)
    return render(request, 'admin/home.html', {'new_cardholders': new_cardholders})

# Cardholders
def view_all_users(request):
    return HttpResponse("View All Users Page")

def manage_user_details(request):
    return render(request, 'cardholder/cardholder-details.html')

def manage_card_holders(request):
    cardholders = CardsEmployee.objects.all()
    return render(request, 'cardholder/cardholder.html', {'cardholders': cardholders})

# EC Card
def issue_card(request):
    return render(request, 'eccard/issue-card.html')

def revoke_card(request):
    return HttpResponse("Revoke Card Page")

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