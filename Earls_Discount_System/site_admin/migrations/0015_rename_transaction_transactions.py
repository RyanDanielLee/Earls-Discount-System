# Generated by Django 5.1.2 on 2024-11-24 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('site_admin', '0014_alter_transaction_card_type_id_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Transaction',
            new_name='Transactions',
        ),
    ]