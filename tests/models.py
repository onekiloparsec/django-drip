from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver


class Profile(models.Model):
    """
    For testing, track the number of "credits".
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    credits = models.PositiveIntegerField(default=0)


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def user_post_save(sender, instance, created, raw, **kwargs):
    if created:
        Profile.objects.create(user=instance)
