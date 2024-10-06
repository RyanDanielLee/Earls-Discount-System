from django.shortcuts import render
from django.http import HttpResponse

# Home route for employee
def employee_home(request):
    return HttpResponse("Employee Home Page")

# My Dashboard - Card Usage
def card_usage(request):
    return HttpResponse("Card Usage Page")

# My Dashboard - My EC Card
def my_ec_card(request):
    return HttpResponse("My EC Card Page")

# My Dashboard - Apply EC Card
def apply_ec_card(request):
    return HttpResponse("Apply EC Card Page")

# Supports - FAQ
def faq(request):
    return HttpResponse("FAQ Page")

# Supports - Report Issues
def report_issues(request):
    return HttpResponse("Report Issues Page")
