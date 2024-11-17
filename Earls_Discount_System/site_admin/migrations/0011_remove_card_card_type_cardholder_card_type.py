# Generated by Django 5.1.2 on 2024-11-17 19:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_admin', '0010_rename_issued_date_cardholder_created_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='card_type',
        ),
        migrations.AddField(
            model_name='cardholder',
            name='card_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardtype'),
        ),
    ]