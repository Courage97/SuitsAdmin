# Generated by Django 5.1.6 on 2025-02-24 06:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_exchangerate_invoice_converted_amount_and_more'),
        ('orders', '0003_alter_salesreport_best_selling_products_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProformaInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('currency', models.CharField(choices=[('USD', 'US Dollar'), ('Bs', 'Bolívares'), ('EUR', 'Euro')], default='USD', max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('finalized', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proforma_invoices', to='orders.order')),
            ],
        ),
    ]
