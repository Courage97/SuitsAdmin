# Generated by Django 5.1.6 on 2025-02-26 22:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('table', '0002_billsplit_orderitem'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together={('table', 'reservation_time')},
        ),
    ]
