from django.db import models

from django.contrib.auth.models import AbstractBaseUser

MALE = 1
FEMALE = 2
NA = 3
ALIEN = 4

GENDER_OPTIONS = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (NA, 'N/A'),
    (ALIEN, 'Alien'),
)


class STLUserManger(models.Manager):

    def get_query_set(self):
        return super(STLUserManger, self).get_query_set().filter(address__city__name__iexact='stl')


class User(AbstractBaseUser):

    name = models.CharField(max_length=200)
    code_name = models.CharField(max_length=400)
    date = models.DateTimeField()
    base_level = models.IntegerField()
    power_level = models.IntegerField()
    gender = models.IntegerField(choices=GENDER_OPTIONS, default=NA)
    update_count = models.IntegerField()

    objects = models.Manager()
    stl_objects = STLUserManger()
