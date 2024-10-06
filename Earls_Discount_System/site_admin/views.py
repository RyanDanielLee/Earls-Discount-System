from django.shortcuts import render
from django.http import HttpResponse

# Home route for admin
def admin_home(request):
    return HttpResponse("Admin Home Page")

# Cardholders
def view_all_users(request):
    return HttpResponse("View All Users Page")

def manage_user_details(request):
    return HttpResponse("Manage User Details Page")

# EC Card
def issue_card(request):
    return HttpResponse("Issue Card Page")

def revoke_card(request):
    return HttpResponse("Revoke Card Page")

def upload_card_faceplates(request):
    return HttpResponse("Upload Card Faceplates Page")

# Reports
def all_pos_transactions(request):
    return HttpResponse("All POS Transactions Page")

def total_discounts_per_store(request):
    return HttpResponse("Total Discounts per Store Page")

def total_discounts_per_employee(request):
    return HttpResponse("Total Discounts per Employee Page")

def view_sent_email_reports(request):
    return HttpResponse("View Sent Email Reports Page")

# Supports
def manage_user_guides(request):
    return HttpResponse("Manage User Guides Page")

def manage_report_issues(request):
    return HttpResponse("Manage Report Issues Page")
