# Generated by Django 5.1.1 on 2024-11-11 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_admin', '0002_alter_financialcalendar_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cardholder',
            name='hire_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='cardtype',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
