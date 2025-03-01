# Generated by Django 5.1.6 on 2025-02-24 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_proformainvoice'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invoice',
            name='status',
        ),
        migrations.AddField(
            model_name='invoice',
            name='seniat_signature_file',
            field=models.FileField(blank=True, null=True, upload_to='invoices/'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='seniat_xml_file',
            field=models.FileField(blank=True, null=True, upload_to='invoices/'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='transmission_status',
            field=models.CharField(choices=[('pending_manual_submission', 'Pending Manual Submission'), ('submitted', 'Submitted to SENIAT')], default='pending_manual_submission', max_length=30),
        ),
    ]
