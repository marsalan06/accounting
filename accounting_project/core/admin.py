# core/admin.py

from django.contrib import admin
from .models import Purchase, Order, OrderItem, FinalTally
import csv
from django.http import HttpResponse

# CSV Export Action


def export_as_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}.csv'
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response


export_as_csv.short_description = "Export Selected as CSV"

# Inline for OrderItem within Order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ['purchase']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'purchase_price',
                    'sale_price', 'purchase_date', 'quantity')
    search_fields = ('id', 'item')
    list_filter = ('purchase_date',)
    actions = [export_as_csv]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'date')
    search_fields = ('id', 'customer_name')
    list_filter = ('date',)
    inlines = [OrderItemInline]
    actions = [export_as_csv]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'purchase', 'quantity_sent')
    search_fields = ('order__id', 'purchase__item')
    autocomplete_fields = ['order', 'purchase']
    actions = [export_as_csv]


@admin.register(FinalTally)
class FinalTallyAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'purchase_amount',
                    'sell_amount', 'profit_loss')
    search_fields = ('order__id',)
    actions = [export_as_csv]
