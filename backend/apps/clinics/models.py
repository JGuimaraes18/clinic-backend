from django.db import models

class Clinic(models.Model):
    name = models.CharField(max_length=255)
    document = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name