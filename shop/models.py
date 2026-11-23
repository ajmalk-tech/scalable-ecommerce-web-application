from django.db import models

# Create your models here.


class AvailableShopID(models.Model):
    code = models.CharField(max_length=4, unique=True)

    def __str__(self):
        return self.name
