from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.generic import CreateView

from eatplusapp.forms import (
    ItemForm,
    CustomerSignupForm)

from eatplusapp.models import (
    Customer,
    Restaurant,
    Item,
    Option,
    Order,
    OrderItem,
    Choice,
    PaymentMethod,
    Manager
)
from allauth.account.views import LoginView, SignupView

# authentications
class MyLoginView(LoginView):
    template_name = 'customer/login.html'


# List of Restaurants
def restaurants_list(request):
    restaurants = Restaurant.objects.all()
    context = {'restaurants': restaurants}
    template = 'customer/restaurants_list.html'
    return render(request, template, context)


def delivery(request, city_slug):
    customer = get_object_or_404(
        Customer, user=request.user, address__city='city_slug')
    restaurant = Restaurant.objects.filter(
        city__city_slug=customer.city.city_slug,
        boundaries__contains=customer.postal_code[:3],
        verified=True,
        available=True
    )
    city_data = restaurant.address.city
    item = Item.objects.filter(available=True, delivery=True)
    order_for = "delivery"
    template = 'city.html'
    context = {
        'restaurants': restaurant, 'item': item, 'city_slug': city_slug,
        'city': city_data, 'order_for': order_for
    }
    return render(request, template, context)


# Menus
@login_required
def pickup_menu(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, restaurant_slug=restaurant_slug)
    order, created = Order.objects.get_or_create(
        restaurant=restaurant,
        customer=get_object_or_404(Customer, user=request.user),
        order_for=1,
        status=1)

    order.total = order.get_total_cost()
    order.sub_total = order.get_sub_total()
    order.save()
    order_items_list = OrderItem.objects.filter(order_id=order.id)
    order_items = {}
    for i in order_items_list:
        order_items[i] = [x.name for x in list(i.choices.all())]

    items = Item.objects.filter(
        restaurant__restaurant_slug=restaurant.restaurant_slug
    )
    payment_methods = PaymentMethod.objects.all()
    add_for = "pickup"
    template = "customer/menu_cart.html"
    context = {
        'restaurant': restaurant, 'items': items, 'order': order,
        'order_items': order_items, 'add_for': add_for,
        'payment_methods': payment_methods
    }

    return render(request, template, context)


# @login_required
def delivery_menu(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, restaurant_slug=restaurant_slug)
    if request.user == True:
        order, created = Order.objects.get_or_create(
            restaurant=restaurant,
            customer=get_object_or_404(Customer, user=request.user),
            order_for=2,
            status=1)
    else:
        order, created = Order.objects.get_or_create(
            restaurant=restaurant,
            order_for=2,
            status=1)
    order.total = order.get_total_cost()
    order.sub_total = order.get_sub_total()
    order.save()
    order_items_list = OrderItem.objects.filter(order_id=order.id)
    order_items = {}
    for i in order_items_list:
        order_items[i] = [x.name for x in list(i.choices.all())]

    items = Item.objects.filter(
        restaurant__restaurant_slug=restaurant.restaurant_slug, delivery=True
    )
    payment_methods = PaymentMethod.objects.all()
    add_for = "delivery"
    template = "customer/menu_cart.html"
    context = {
        'restaurant': restaurant, 'items': items, 'order': order,
        'order_items': order_items, 'add_for': add_for,
        'payment_methods': payment_methods
    }

    return render(request, template, context)


# display item's options. e.g : size: large, medium and small
def item_option(request, item_id, order_id, restaurant_id):
    option = Option.objects.filter(item_id=item_id)
    order = get_object_or_404(Order, id=order_id)
    add_for = order.order_for
    restaurant = order.restaurant
    item = Item.objects.filter(restaurant__id=restaurant_id)
    order_item = OrderItem.objects.filter(order_id=order.id)
    item = Item.objects.get(pk=item_id)
    form = ItemForm(item=item)

    if request.method == "POST":
        order_item = OrderItem()
        order_item.restaurant = item.restaurant
        order_item.item = item

        order_item.quantity = request.POST.get("quantity")
        order_item.order_id = order.id
        order_item.price = item.price
        order_item.save()

        for field_name in form.fields:
            choices = request.POST.getlist(field_name)
            for _choice in choices:
                choice = Choice.objects.get(pk=_choice)
                order_item.choices.add(choice)
        order_item.save()

        if order.order_for == 2:
            return redirect(
                'delivery_menu',
                restaurant_slug=item.restaurant.restaurant_slug
            )
        if order.order_for == 1:
            return redirect(
                'pickup_menu', restaurant_slug=item.restaurant.restaurant_slug
            )

    template = 'menu.html'
    context = {
        'item': item, 'order': order, 'order_item': order_item, 'options': option,
        'form': form, 'add_for': add_for, 'restaurant': restaurant
    }

    return render(request, template, context)


def order_create(request, order_id):
    action = request.GET.get("action")
    if action == "payment":
        try:
            order = Order.objects.get(pk=order_id)
            order.payment_method_id = int(request.POST.get("payment_method"))
            order.save()
        except Order.DoesNotExist:
            pass
        finally:
            return HttpResponse(content="")

    order = get_object_or_404(Order, id=order_id)
    if (
        order.order_for == 2 and
        order.sub_total > order.restaurant.minimum_delivery_order
    ):
        order.status = 3
        order.sub_total += order.restaurant.delivery_fee
        order.total = (
            order.sub_total / 100 * order.restaurant.city.province.tax
        )
        order.save()
    elif order.order_for == 1:
        order.status = 3
        order.save()
    else:
        return redirect(request.META['HTTP_REFERER'])
    return redirect('order_list')


def add_choice(request, choice_id, order_id, item_id, option_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 1
    order.save()
    item = get_object_or_404(Item, id=item_id)
    choice = Choice.objects.get(id=choice_id)
    option = get_object_or_404(Option, id=option_id)
    item, created = OrderItem.objects.get_or_create(
        order=order,
        item=item,
        option=option,
        sub_total=item.price
    )

    if item.quantity == 0 and option.type == 0:
        item.quantity += 1
        item.choices.add(choice)
    elif item.quantity == 0 and option.type == 1:
        item.quantity += 1
        item.choices.add(choice)
    else:
        item.choices.add(choice)

    item.save()

    return redirect(request.META.get['HTTP_REFERER'])


def cart_add(request, order_id, item_id, action):
    option = Option.objects.filter(item_id=item_id)
    order = get_object_or_404(Order, id=order_id)
    item = get_object_or_404(Item, id=item_id)

    if option:
        return redirect(
            'item_option',
            order_id=order.id,
            item_id=item_id,
            restaurant_id=item.restaurant.id
        )

    item, created = OrderItem.objects.get_or_create(
        order=order,
        restaurant=item.restaurant,
        item=item,
        sub_total=item.price
    )
    if action == "plus":
        item.quantity += 1
    elif action == "mines":
        item.quantity -= 1
    elif action == "add" and item.quantity == 0:
        item.quantity += 1
    item.save()

    return HttpResponse()


def cart_remove(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    item.delete()
    return redirect(request.META['HTTP_REFERER'])


class CustomerSignUpView (SignupView):
    form_class = CustomerSignupForm
    template_name = 'customer/signup.html'

    def get_form_class(self):
        return self.form_class

    def get_success_url(self):
        return reverse('restaurants')  # TODO: change to city view when available
