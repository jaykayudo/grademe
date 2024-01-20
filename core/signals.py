from rolepermissions.roles import assign_role
from rolepermissions.checkers import has_role
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import ChiefAdmin


@receiver(post_save,sender=ChiefAdmin)
def add_chiefadmin_role(sender, instance, **kwargs):
    if not instance.user:
        return 
    if not has_role(instance.user,"chief_admin"):
        assign_role(instance.user,"chief_admin")
    