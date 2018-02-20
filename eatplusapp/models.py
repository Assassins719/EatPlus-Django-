from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.template.defaultfilters import slugify


# Create your models here.
class Address(models.Model):
    country = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    city_slug = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Address'

    def __str__(self):
        return self.country

    def save(self, *args, **kwargs):
        self.city_slug = slugify(self.city)
        super(Address, self).save(*args, **kwargs)


class PaymentMethod(models.Model):
    method = models.CharField(max_length=250)

    def __str__(self):
        return self.method


class Restaurant(models.Model):
    name = models.CharField(max_length=500)
    phone = models.CharField(max_length=500)
    logo = models.ImageField(upload_to='images/restaurants/', blank=True)
    restaurant_slug = models.SlugField(max_length=250, unique=True)
    pickup_payment_methods = models.ManyToManyField(
        PaymentMethod,
        related_name='pickup_restaurant_payment',
        blank=True
    )
    delivery_payment_methods = models.ManyToManyField(
        PaymentMethod,
        related_name='delivery_restaurant_payment',
        blank=True
    )
    minimum_delivery_order = models.IntegerField(blank=True, null=True)
    delivery_fee = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    verification_code = models.CharField(max_length=4, blank=True)
    verified = models.BooleanField(default=False)
    available = models.BooleanField(default=False)
    boundaries = models.TextField(blank=True)
    address = models.ForeignKey(Address, related_name='address_restaurant')
    referral_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.restaurant_slug = slugify(self.name)
        super(Restaurant, self).save(*args, **kwargs)


class MenuSection(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name="restaurant_menu")
    title = models.CharField(max_length=250)
    order = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)]
    )

    class Meta:
        unique_together = ('restaurant', 'order')

    def __str__(self):
        return self.title


class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer'
    )
    image = models.ImageField(upload_to='images/customers/', blank=False)
    phone = models.CharField(max_length=500, blank=True)
    address = models.ForeignKey(Address, related_name='address_customer')

    def __str__(self):
        return self.user.username


class Manager(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='manager'
    )
    restaurant = models.OneToOneField(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='manager'
    )

class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    menu_section = models.ForeignKey(MenuSection, related_name="meal_section")
    order = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    name = models.CharField(max_length=500)
    short_description = models.CharField(max_length=500)
    image = models.ImageField(upload_to='images/items/', blank=False)
    price = models.IntegerField(default=0)
    available = models.BooleanField(default=False)
    delivery = models.BooleanField(default=False)
    takeout = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('menu_section', 'order')


class Option(models.Model):
    item = models.ForeignKey(Item, related_name='meal_option')
    name = models.CharField(max_length=500)
    type = models.IntegerField(choices=((0, "radio"), (1, "select")))

    def __str__(self):
        return self.name


class Choice(models.Model):
    item = models.ForeignKey(Item, related_name='item_choice')
    option = models.ForeignKey(Option, related_name='option_choice')
    name = models.CharField(max_length=500)
    default = models.BooleanField(default=False)
    extra_charge = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.name


class Order(models.Model):
    OPEN = 1
    PLACED = 2
    RECEIVED = 3
    READY = 4
    ONTHEWAY = 5
    COMPLETED = 6
    CANCELLED = 7

    PICKUP = 1
    DELIVERY = 2

    STATUS_CHOICES = (
        (OPEN, "Open"),
        (PLACED, "Placed"),
        (RECEIVED, "Received"),
        (READY, "Ready"),
        (ONTHEWAY, "On the way"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    )

    ORDER_CHOICES = (
        (PICKUP, "Pick up"),
        (DELIVERY, "Delivery"),
    )

    customer = models.ForeignKey(Customer, related_name="order_customer", null=True, blank=True)
    restaurant = models.ForeignKey(Restaurant)
    address = models.CharField(max_length=500, blank=True)
    total = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)
    order_for = models.IntegerField(
        choices=ORDER_CHOICES,
        blank=True, null=True
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=PLACED)
    created_at = models.DateTimeField(auto_now_add=True)
    picked_at = models.DateTimeField(blank=True, null=True)
    note = models.CharField(max_length=1000, blank=True)
    payment_method = models.ForeignKey(
        PaymentMethod,
        related_name='order_payment',
        default=1
    )

    def __str__(self):
        return 'Order {}'.format(self.id)

    def get_sub_total(self):
        sub_total = sum(item.get_cost() for item in self.order_orderitem.all())
        return sub_total

# todo: make list of taxes
    def get_total_cost(self):
        total = self.get_sub_total() / 100 * 13
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_orderitem')
    item = models.ForeignKey(Item, related_name='item_orderitem')
    choices = models.ManyToManyField(
        Choice,
        related_name='choices_orderitem',
        blank=True
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sub_total = models.IntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        cost = sum(
            [self.item.price] + [
                choices.extra_charge for choices in self.choices.all()
            ]
        ) * self.quantity

        return round(cost, 2)
