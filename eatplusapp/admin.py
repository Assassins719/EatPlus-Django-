from django.contrib import admin
from eatplusapp.models import (
    Restaurant,
    Item,
    Order,
    Choice,
    Option,
    MenuSection,
    OrderItem,
    Customer,
    Address,
    PaymentMethod
)

# Register your models here.
admin.site.register(Restaurant),
admin.site.register(Item),
admin.site.register(Order),
admin.site.register(Choice),
admin.site.register(Option),
admin.site.register(MenuSection),
admin.site.register(OrderItem),
admin.site.register(Customer),
admin.site.register(Address),
admin.site.register(PaymentMethod)
