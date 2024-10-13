from django.db import models

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    status = models.CharField(
        max_length=10,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active'
    )
    card_type = models.CharField(max_length=10)  # e.g., EC10, EC50, EC100
    concept = models.CharField(max_length=50)  # internal or external

    def __str__(self):
        return f"{self.name} ({self.status})"


class Card(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    issued_date = models.DateTimeField(auto_now_add=True)
    revoked_date = models.DateTimeField(null=True, blank=True)
    digital_wallet = models.BooleanField(default=True)
    card_faceplate = models.URLField(max_length=255)

    def __str__(self):
        return f"Card for {self.employee.name}"


class Transaction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    store_id = models.IntegerField()
    discount_applied = models.FloatField()
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction by {self.employee.name} on {self.transaction_date}"


class StoreReference(models.Model):
    store_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.store_name

