from django.shortcuts import render

from django.http import HttpResponse

# Simple placeholder view for the login page
def login_view(request):
    return HttpResponse("Login Page")
