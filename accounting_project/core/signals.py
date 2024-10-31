# core/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem, FinalTally


@receiver(post_save, sender=Order)
def create_or_update_final_tally(sender, instance, created, **kwargs):
    if created:
        # Create a FinalTally when a new Order is created
        FinalTally.objects.create(order=instance)
    else:
        # Update the existing FinalTally when the Order is updated
        try:
            instance.finaltally.save()
        except FinalTally.DoesNotExist:
            # Create FinalTally if it doesn't exist
            FinalTally.objects.create(order=instance)


@receiver(post_save, sender=OrderItem)
def update_final_tally_on_orderitem_save(sender, instance, created, **kwargs):
    try:
        tally = instance.order.finaltally
    except FinalTally.DoesNotExist:
        # Create FinalTally if it doesn't exist
        tally = FinalTally.objects.create(order=instance.order)
    tally.save()


@receiver(post_delete, sender=OrderItem)
def update_final_tally_on_orderitem_delete(sender, instance, **kwargs):
    try:
        tally = instance.order.finaltally
    except FinalTally.DoesNotExist:
        # Create FinalTally if it doesn't exist
        tally = FinalTally.objects.create(order=instance.order)
    tally.save()
