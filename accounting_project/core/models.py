# core/models.py

import uuid
from django.db import models
from django.db.models import Sum, F, DecimalField
from django.utils import timezone
from django.core.exceptions import ValidationError


class Purchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.CharField(max_length=255)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()
    quantity = models.IntegerField(default=0)
    picture = models.ImageField(upload_to='pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.item} ({self.id})"


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.customer_name}"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, related_name='order_items', on_delete=models.CASCADE)
    purchase = models.ForeignKey(
        Purchase, related_name='order_items', on_delete=models.CASCADE)
    quantity_sent = models.IntegerField()

    def __str__(self):
        return f"{self.purchase.item} x {self.quantity_sent}"

    def clean(self):
        # Optional: Prevent ordering negative quantities or other validations
        if self.quantity_sent <= 0:
            raise ValidationError({
                'quantity_sent': "Quantity sent must be greater than zero."
            })

    def save(self, *args, **kwargs):
        """
        Override the save method to update the Purchase.quantity.
        Allows Purchase.quantity to go negative to indicate reordering needs.
        """
        self.full_clean()  # Validate the instance before saving

        if self.pk:
            # Existing instance; retrieve the original to calculate the difference
            try:
                original = OrderItem.objects.get(pk=self.pk)
                quantity_diff = self.quantity_sent - original.quantity_sent
            except OrderItem.DoesNotExist:
                # If the original doesn't exist, treat this as a new instance
                quantity_diff = self.quantity_sent
        else:
            # New instance
            quantity_diff = self.quantity_sent

        # Save the OrderItem first
        super().save(*args, **kwargs)

        # Update Purchase.quantity
        self.purchase.quantity -= quantity_diff
        self.purchase.save()

    def delete(self, *args, **kwargs):
        """
        Override the delete method to revert the Purchase.quantity.
        """
        # Update Purchase.quantity before deletion
        self.purchase.quantity += self.quantity_sent
        self.purchase.save()
        super().delete(*args, **kwargs)


class FinalTally(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    purchase_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    sell_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    profit_loss = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Tally for {self.order.id}"

    def save(self, *args, **kwargs):
        """
        Override the save method to calculate purchase_amount, sell_amount, and profit_loss.
        """
        # Calculate purchase_amount and sell_amount based on OrderItems
        purchase_sum = self.order.order_items.aggregate(
            total=Sum(F('purchase__purchase_price') *
                      F('quantity_sent'), output_field=DecimalField())
        )['total'] or 0
        sell_sum = self.order.order_items.aggregate(
            total=Sum(F('purchase__sale_price') * F('quantity_sent'),
                      output_field=DecimalField())
        )['total'] or 0
        profit_loss = sell_sum - purchase_sum

        self.purchase_amount = purchase_sum
        self.sell_amount = sell_sum
        self.profit_loss = profit_loss

        super().save(*args, **kwargs)
