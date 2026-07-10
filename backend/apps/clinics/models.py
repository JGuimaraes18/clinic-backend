from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Clinic(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    document = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Customization fields
    logo = models.FileField(upload_to="clinic_media/logos/", null=True, blank=True)
    banner = models.FileField(upload_to="clinic_media/banners/", null=True, blank=True)
    theme = models.CharField(max_length=20, default="SYSTEM")
    primary_color = models.CharField(max_length=20, default="#0651ED")
    secondary_color = models.CharField(max_length=20, default="#4F46E5")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug

            while Clinic.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{get_random_string(4)}"

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name