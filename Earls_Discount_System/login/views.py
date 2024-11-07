from django.shortcuts import render

# Simple placeholder view for the login page
def login_view(request):
    return render(request, 'login/login.html')
