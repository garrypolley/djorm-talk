from django.db import models

from user.models import User

# Create your models here.


class Address(models.Model):

    street = models.CharField(max_length=200)
    user = models.ForeignKey(User)
    gangsta_users = models.ManyToManyField(User, null=True, blank=True, related_name="gangstas")


class City(models.Model):

    address = models.ForeignKey(Address)
    name = models.CharField(max_length=300)
