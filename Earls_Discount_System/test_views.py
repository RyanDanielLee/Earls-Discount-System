import pytest
from django.urls import reverse
from django.utils.timezone import now, timedelta
from site_admin.views import (Cardholder, CardType, Company, Card, WalletSelectionToken)
from unittest.mock import patch

@pytest.mark.django_db
def test_admin_home(client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")
    cardholder = Cardholder.objects.create(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        company=company,
        card_type=card_type,
        created_date=now(),
        is_active=True
    )

    response = client.get(reverse('admin_home'))

    assert response.status_code == 200
    assert "John Doe" in response.content.decode()

@pytest.mark.django_db
def test_manage_user_details(client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")
    cardholder = Cardholder.objects.create(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        company=company,
        card_type=card_type,
        is_active=True
    )

    response = client.get(reverse('manage_user_details', args=[cardholder.id]))


    assert response.status_code == 200
    assert "Jane Smith" in response.content.decode()

@pytest.mark.django_db
def test_manage_card_holders(client):

    company = Company.objects.create(name="Joey")
    card_type = CardType.objects.create(name="EC50")
    Cardholder.objects.create(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        company=company,
        card_type=card_type,
        is_active=True
    )

    response = client.get(reverse('manage_card_holders'))


    assert response.status_code == 200
    assert "John Doe" in response.content.decode()

@pytest.mark.django_db
def test_search_cardholders(client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")
    Cardholder.objects.create(
        first_name="Alice",
        last_name="Johnson",
        email="alice.johnson@example.com",
        company=company,
        card_type=card_type
    )

    response = client.get(reverse('search_cardholders'), {'q': 'Alice', 'filter_by': 'name'})


    assert response.status_code == 200
    assert "Alice Johnson" in response.content.decode()

@pytest.mark.django_db
@patch('site_admin.views.send_wallet_selection_email')
def test_issue_card(mock_send_wallet_email, client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")

    response = client.post(reverse('issue_card'), {
        'first_name': 'Bob',
        'last_name': 'Builder',
        'email': 'bob.builder@example.com',
        'company': company.id,
        'card_type': card_type.id,
        'note': 'Test Note'
    })


    assert response.status_code == 302  # Redirect to manage_card_holders
    assert Cardholder.objects.count() == 1
    assert Card.objects.count() == 1
    assert WalletSelectionToken.objects.count() == 2
    mock_send_wallet_email.assert_called_once()

@pytest.mark.django_db
def test_revoke_card(client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")
    cardholder = Cardholder.objects.create(
        first_name="Test",
        last_name="User",
        email="test.user@example.com",
        company=company,
        card_type=card_type,
        is_active=True
    )
    card = Card.objects.create(cardholder=cardholder, card_number=123456789, issued_date=now())

    response = client.post(reverse('revoke_card', args=[cardholder.id]))

    card.refresh_from_db()
    cardholder.refresh_from_db()
    assert response.status_code == 302  # Redirect to manage_user_details
    assert card.card_number is None
    assert not cardholder.is_active

@pytest.mark.django_db
def test_delete_cardholder(client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")
    cardholder = Cardholder.objects.create(
        first_name="Test",
        last_name="User",
        email="test.user@example.com",
        company=company,
        card_type=card_type
    )
    Card.objects.create(cardholder=cardholder, card_number=123456789)

    response = client.post(reverse('delete_cardholder', args=[cardholder.id]))

    assert response.status_code == 302  # Redirect to manage_card_holders
    assert Cardholder.objects.count() == 0
    assert Card.objects.count() == 0

@pytest.mark.django_db
@patch('site_admin.views.send_wallet_selection_email')
def test_reissue_card(mock_send_wallet_email, client):

    company = Company.objects.create(name="Earls")
    card_type = CardType.objects.create(name="EC50")
    cardholder = Cardholder.objects.create(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        company=company,
        card_type=card_type,
        is_active=False
    )
    card = Card.objects.create(cardholder=cardholder, card_number=None)

    response = client.post(reverse('reissue_card', args=[cardholder.id]))

    card.refresh_from_db()
    cardholder.refresh_from_db()
    assert response.status_code == 302  # Redirect to manage_user_details
    assert card.card_number is not None
    assert cardholder.is_active
    mock_send_wallet_email.assert_called_once()