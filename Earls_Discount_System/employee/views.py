from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.http import HttpResponse


# Helper function to check if the user belongs to a specific group
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def user_required(view_func):
    # Redirect to access-denied page if user is not in the 'user' group
    return user_passes_test(lambda u: in_group(u, 'user'), login_url='/employee/access-denied/')(view_func)


def staff_required(view_func):
    # Redirect to access-denied page if the user is not staff
    return user_passes_test(lambda u: u.is_staff, login_url='/employee/access-denied/')(view_func)


# Access Denied view
def access_denied(request):
    return HttpResponse("You do not have permission to view this page.", status=403)


@user_required
def employee_home(request):
    return HttpResponse("Employee Home Page")


@user_required
def card_usage(request):
    return HttpResponse("Card Usage Page")


@user_required
def my_ec_card(request):
    return HttpResponse("My EC Card Page")


@staff_required
def apply_ec_card(request):
    return HttpResponse("Apply EC Card Page")


@user_required
def faq(request):
    return HttpResponse("FAQ Page")


@user_required
def report_issues(request):
    return HttpResponse("Report Issues Page")
