# Generated by Django 5.0.7 on 2024-07-18 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_imagemodel_createdate'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('patientId', models.IntegerField()),
                ('createDate', models.DateField(auto_now_add=True)),
                ('memory', models.IntegerField()),
                ('orientation', models.IntegerField()),
                ('judgment', models.IntegerField()),
                ('community', models.IntegerField()),
                ('hobbies', models.IntegerField()),
                ('personalCare', models.IntegerField()),
                ('cdrValues', models.IntegerField()),
            ],
        ),
        migrations.RenameField(
            model_name='patient',
            old_name='id',
            new_name='patientId',
        ),
    ]
