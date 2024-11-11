# Generated by Django 5.1.2 on 2024-11-11 07:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CardType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
                'db_table': 'card_type',
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
                'db_table': 'company',
            },
        ),
        migrations.CreateModel(
            name='FaceplateImage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('wallet_type', models.CharField(max_length=50)),
                ('image_type', models.CharField(max_length=50)),
                ('uploaded_date', models.DateField()),
            ],
            options={
                'db_table': 'faceplate_image',
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('short_name', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'store',
            },
        ),
        migrations.CreateModel(
            name='Cardholder',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('hire_date', models.DateField(null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('issued_date', models.DateField()),
                ('card_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardtype')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.company')),
            ],
            options={
                'db_table': 'cardholder',
            },
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('card_number', models.CharField(max_length=20, unique=True)),
                ('issued_date', models.DateField()),
                ('revoked_date', models.DateField(blank=True, null=True)),
                ('cardholder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardholder')),
                ('card_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardtype')),
            ],
            options={
                'db_table': 'card',
            },
        ),
        migrations.CreateModel(
            name='FinancialCalendar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calendar_date', models.DateField(unique=True)),
                ('year', models.IntegerField()),
                ('period', models.IntegerField()),
                ('week', models.IntegerField()),
            ],
            options={
                'db_table': 'financial_calendar',
                'unique_together': {('year', 'period', 'week')},
            },
        ),
        migrations.CreateModel(
            name='TotalDiscountEmployee',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('total_discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('visit_count', models.IntegerField()),
                ('cardholder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardholder')),
            ],
            options={
                'db_table': 'total_discount_employee',
            },
        ),
        migrations.CreateModel(
            name='TotalDiscountStore',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('total_discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.store')),
            ],
            options={
                'db_table': 'total_discount_store',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('business_date', models.DateField()),
                ('check_number', models.CharField(max_length=20)),
                ('check_name', models.CharField(max_length=100)),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tip_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('card_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardtype')),
                ('cardholder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.cardholder')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='site_admin.store')),
            ],
            options={
                'db_table': 'transaction',
                'unique_together': {('store', 'business_date', 'check_number')},
            },
        ),
    ]
