from django.db import models
from django.contrib.auth.models import User
import datetime

class Patient(models.Model):
    patientId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100,null=True)
    age = models.IntegerField(null=True)
    emergencyContact = models.CharField(max_length=100,null=True)
    caretakerId = models.CharField(max_length=50, default='',null=True) 
    pincode = models.CharField(max_length=20,null=True)

    def __str__(self):
        return str(self.name)

class Activation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)

class ImageModel(models.Model):
    imageId = models.AutoField(primary_key=True)
    image = models.BinaryField()
    patientId = models.CharField(max_length=20)
    createDate = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return str(self.imageId)

    def save(self, *args, **kwargs):
        # Ensure createDate is formatted as dd-mm-yyyy before saving
        self.createDate = datetime.datetime.now().strftime('%d-%m-%Y')
        super().save(*args, **kwargs)

class SurveyModel(models.Model):
    id = models.AutoField(primary_key=True)
    patientId = models.IntegerField(null=True)
    createDate =  models.DateField()
    memory = models.FloatField(null=True)
    orientation = models.FloatField(null=True)
    judgment = models.FloatField(null=True)
    community = models.FloatField(null=True)
    hobbies = models.FloatField(null=True)
    personalCare = models.FloatField(null=True)
    cdrValues = models.FloatField(null=True)   

    def __str__(self):
        return str(self.id)

    # def save(self, *args, **kwargs):
    #     # Ensure createDate is formatted as dd-mm-yyyy before saving
    #     self.createDate = datetime.datetime.now().strftime('%d-%m-%Y')
    #     super().save(*args, **kwargs)

    