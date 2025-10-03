from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser."""
    # Add custom fields here if needed
    bio = models.TextField(blank=True, default='')

    def __str__(self):
        return self.username