# Generated by Django 5.0.7 on 2024-07-18 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_alter_patient_caretakerid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveymodel',
            name='createDate',
            field=models.DateField(),
        ),
    ]