from django.db import models

class ContactModel(models.Model):
    """

    """
    name = models.CharField(null=False,max_length=255)
    email = models.EmailField(null=False,max_length=255)
