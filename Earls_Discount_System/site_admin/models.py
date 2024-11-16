from django.db import models
from django.utils import timezone
import uuid

# class AuthUser(models.Model):
#     password = models.CharField(max_length=128)
#     last_login = models.DateTimeField(blank=True, null=True)
#     is_superuser = models.IntegerField()
#     username = models.CharField(unique=True, max_length=150)
#     first_name = models.CharField(max_length=150)
#     last_name = models.CharField(max_length=150)
#     email = models.CharField(max_length=254)
#     is_staff = models.IntegerField()
#     is_active = models.IntegerField()
#     date_joined = models.DateTimeField()

#     class Meta:
#         db_table = 'auth_user'


# class DjangoMigrations(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     app = models.CharField(max_length=255)
#     name = models.CharField(max_length=255)
#     applied = models.DateTimeField()

#     class Meta:
#         db_table = 'django_migrations'


# class DjangoSession(models.Model):
#     session_key = models.CharField(primary_key=True, max_length=40)
#     session_data = models.TextField()
#     expire_date = models.DateTimeField()

#     class Meta:
#         db_table = 'django_session'

# Custom tables
class FinancialCalendar(models.Model):
    id = models.AutoField(primary_key=True)
    calendar_date = models.DateField(unique=True)
    year = models.IntegerField()
    period = models.IntegerField()
    week = models.IntegerField()

    class Meta:
        db_table = 'financial_calendar'
        unique_together = ('year', 'period', 'week')

class Store(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20)

    class Meta:
        db_table = 'store'

class CardType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'card_type'

class Company(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'company'

class Cardholder(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    note = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    card_type = models.ForeignKey('CardType', on_delete=models.CASCADE)
    issued_date = models.DateField()

    class Meta:
        db_table = 'cardholder'

class Card(models.Model):
    id = models.AutoField(primary_key=True)
    card_number = models.IntegerField(unique=True)
    issued_date = models.DateField()
    revoked_date = models.DateField(null=True, blank=True)
    cardholder = models.ForeignKey('Cardholder', on_delete=models.CASCADE)
    card_type = models.ForeignKey('CardType', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'card'
 
class DigitalWallet(models.Model):
    id = models.AutoField(primary_key=True)
    card_number = models.OneToOneField('Card', on_delete=models.CASCADE, related_name='digital_wallets')
    wallet_type = models.CharField(max_length=50)  # 'Apple Wallet' or 'Google Wallet'
    issued_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'digital_wallet'

class WalletSelectionToken(models.Model):
    cardholder = models.ForeignKey('Cardholder', on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class FaceplateImage(models.Model):
    id = models.AutoField(primary_key=True)
    wallet_type = models.CharField(max_length=50) # 'Google Wallet', 'Apple Wallet'
    image_type = models.CharField(max_length=50) # 'logo', 'icon'
    uploaded_date = models.DateField()

    class Meta:
        db_table = 'faceplate_image'

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    store = models.ForeignKey('Store', on_delete=models.CASCADE)
    business_date = models.DateField()
    check_number = models.CharField(max_length=20)
    check_name = models.CharField(max_length=50)
    cardholder = models.ForeignKey('Cardholder', on_delete=models.CASCADE)
    card_type = models.ForeignKey('CardType', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'transaction'
        unique_together = (('store', 'business_date', 'check_number'),)

class TotalDiscountStore(models.Model):
    id = models.AutoField(primary_key=True)
    store = models.ForeignKey('Store', on_delete=models.CASCADE)
    total_discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'total_discount_store'

class TotalDiscountEmployee(models.Model):
    id = models.AutoField(primary_key=True)
    cardholder = models.ForeignKey('Cardholder', on_delete=models.CASCADE)
    total_discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    visit_count = models.IntegerField()

    class Meta:
        db_table = 'total_discount_employee'

# class CardsCard(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     issued_date = models.DateTimeField()
#     revoked_date = models.DateTimeField(blank=True, null=True)
#     digital_wallet = models.IntegerField()
#     card_faceplate = models.CharField(max_length=255)
#     employee = models.ForeignKey('CardsEmployee', models.DO_NOTHING)

#     class Meta:
#         managed = True
#         db_table = 'cards_card'


# class CardsEmployee(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=100)
#     email = models.CharField(max_length=254)
#     status = models.CharField(max_length=10)
#     card_type = models.CharField(max_length=10)
#     concept = models.CharField(max_length=50)
#     issue_date = models.DateField(blank=True, null=True)

#     class Meta:
#         managed = True
#         db_table = 'cards_employee'


# class CardsStorereference(models.Model):
#     store_id = models.BigAutoField(primary_key=True)
#     store_name = models.CharField(max_length=100)
#     short_name = models.CharField(max_length=100)

#     class Meta:
#         managed = True
#         db_table = 'cards_storereference'


# class CardsTransaction(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     store_id = models.IntegerField()
#     discount_applied = models.FloatField()
#     transaction_date = models.DateTimeField()
#     employee = models.ForeignKey(CardsEmployee, models.DO_NOTHING)

#     class Meta:
#         managed = True
#         db_table = 'cards_transaction'


# class AuthGroup(models.Model):
#     name = models.CharField(unique=True, max_length=150)

#     class Meta:
#         managed = False
#         db_table = 'auth_group'

# class AuthGroupPermissions(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
#     permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

#     class Meta:
#         managed = False
#         db_table = 'auth_group_permissions'
#         unique_together = (('group', 'permission'),)

# class AuthPermission(models.Model):
#     name = models.CharField(max_length=255)
#     content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
#     codename = models.CharField(max_length=100)

#     class Meta:
#         managed = False
#         db_table = 'auth_permission'
#         unique_together = (('content_type', 'codename'),)

# class AuthUserGroups(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(AuthUser, models.DO_NOTHING)
#     group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

#     class Meta:
#         managed = False
#         db_table = 'auth_user_groups'
#         unique_together = (('user', 'group'),)

# class AuthUserUserPermissions(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(AuthUser, models.DO_NOTHING)
#     permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

#     class Meta:
#         managed = False
#         db_table = 'auth_user_user_permissions'
#         unique_together = (('user', 'permission'),)

# class DjangoAdminLog(models.Model):
#     action_time = models.DateTimeField()
#     object_id = models.TextField(blank=True, null=True)
#     object_repr = models.CharField(max_length=200)
#     action_flag = models.PositiveSmallIntegerField()
#     change_message = models.TextField()
#     content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
#     user = models.ForeignKey(AuthUser, models.DO_NOTHING)

#     class Meta:
#         managed = False
#         db_table = 'django_admin_log'

# class DjangoContentType(models.Model):
#     app_label = models.CharField(max_length=100)
#     model = models.CharField(max_length=100)

#     class Meta:
#         managed = False
#         db_table = 'django_content_type'
#         unique_together = (('app_label', 'model'),)


