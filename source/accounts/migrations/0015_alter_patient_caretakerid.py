# Generated by Django 5.0.7 on 2024-07-18 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_alter_patient_age_alter_patient_emergencycontact_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='caretakerId',
            field=models.CharField(default='', max_length=50, null=True),
        ),
    ]