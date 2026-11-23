from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.


class CustomUser(AbstractUser):
    is_shop = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)


class ShopProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop_profile"
    )
    profile_pic = models.ImageField(
        upload_to="shop_profile_pic/", null=True, blank=True
    )
    shop_address = models.TextField(null=True, blank=True)


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    profile_pic = models.ImageField(
        upload_to="customer_profile_pic/", null=True, blank=True
    )
    delivery_address = models.TextField(null=True, blank=True)
