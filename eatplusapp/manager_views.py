from django.contrib.auth import authenticate, login
from eatplusapp.forms import *
from eatplusapp.models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from allauth.account.views import SignupView
from django.urls import reverse
from eatplusapp.forms import AddressForm, RestaurantForm

@login_required(login_url='/restaurant/sign-in/')
def restaurant_manager(request):
    return redirect(restaurant_order)


@login_required(login_url='/restaurant/sign-in/')
def restaurant_account(request):

    if request.method == "POST":
        user_form = UserFormForEdit(request.POST, instance=request.user)
        restaurant_form = RestaurantSetting(
            request.POST, request.FILES, instance=request.user.restaurant
        )

        if user_form.is_valid() and restaurant_form.is_valid():
            user_form = user_form.save(commit=False)
            restaurant_form = restaurant_form.save(commit=False)
            user_form.save()
            restaurant_form.save()

            return redirect('restaurant-account')

    else:
        user_form = UserFormForEdit(instance=request.user)
        restaurant_form = RestaurantSetting(instance=request.user.restaurant)

    template = 'restaurant/account.html'
    context = {
        "user_form": user_form,
        "restaurant_form": restaurant_form
    }

    return render(request, template, context)


@login_required(login_url='/restaurant/sign-in/')
def restaurant_section(request):
    form = MenuSectionForm()

    if request.method == "POST":
        form = MenuSectionForm(request.POST, request.FILES)

        if form.is_valid():
            section = form.save(commit=False)
            section.restaurant = request.user.restaurant
            section.save()

            return redirect(manager_menu)

    return render(request, 'restaurant/menu_section.html', {"form": form})


@login_required(login_url='/restaurant/sign-in/')
def menu(request):
    section = MenuSection.objects.filter(
        restaurant=request.user.manager.restaurant
    ).order_by("order")
    items = [
        list(Item.objects.filter(menu_section=c).order_by('order'))
        for c in section
    ]
    items = filter(lambda l: len(l) > 0, items)

    return render(
        request,
        'manager/menu/menu.html',
        {"items": items, "sections": section}
    )


@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_item(request, section_id):
    form = NewItemForm()

    if request.method == "POST":
        form = NewItemForm(request.POST, request.FILES)

        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = request.user.restaurant
            item.menu_section = get_object_or_404(MenuSection, id=section_id)
            item.save()

            return redirect(restaurant_item)

    return render(request, 'restaurant/add_item.html', {"form": form})


@login_required(login_url='/restaurant/sign-in/')
def restaurant_edit_item(request, item_id):
    form = NewItemForm(instance=Item.objects.get(id=item_id))

    if request.method == "POST":
        form = NewItemForm(
            request.POST, request.FILES, instance=Item.objects.get(id=item_id)
        )

        if form.is_valid():
            form.save()
            return redirect(restaurant_item)

    return render(request, 'restaurant/edit_item.html', {"form": form})


@login_required(login_url='/restaurant/sign-in/')
def create_option(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        form = OptionForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.item = item
            form.save()

            return redirect('restaurant-item')

    else:
        form = OptionForm()

    template = "restaurant/create_option.html"
    context = {'item': item, 'form': form}

    return render(request, template, context)


@login_required(login_url='/restaurant/sign-in/')
def create_choice(request, option_id):
    option = get_object_or_404(Option, id=option_id)

    if request.method == "POST":
        form = ChoiceForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.item = option.item
            form.option = option
            form.save()

            return redirect('restaurant-item')
    else:
        form = ChoiceForm()

    template = "restaurant/create_choice.html"
    context = {'option': option, 'form': form}

    return render(request, template, context)


@login_required(login_url='/restaurant/sign-in/')
def restaurant_order(request):
    if request.method == "POST":
        order = Order.objects.get(
            id=request.POST["id"], restaurant=request.user.restaurant
        )

        if order.status == Order.PLACED:
            order.status = Order.RECEIVED
            order.save()

        elif order.status == Order.RECEIVED:
            order.status = Order.READY
            order.save()

        elif order.status == Order.READY and order.order_for == 1:
            order.status = Order.COMPLETED
            order.save()

        elif order.status == Order.READY and order.order_for == 2:
            order.status = Order.ONTHEWAY
            order.save()

        elif order.status == Order.ONTHEWAY and order.order_for == 2:
            order.status = Order.COMPLETED
            order.save()

    orders = Order.objects.filter(
        restaurant=request.user.restaurant
    ).order_by("-created_at").exclude(status__lte=2)

    return render(request, 'restaurant/order.html', {"orders": orders})


def create_restaurant(request):
    if request.method == "POST":
        restaurant_form = RestaurantForm(request.POST, prefix="restaurant")
        address_form = AddressForm(request.POST, prefix="address")
        if address_form.is_valid() and restaurant_form.is_valid():
            address = address_form.save()
            restaurant = restaurant_form.save(commit=False)
            restaurant.address = address
            restaurant.save()
            return redirect('manager_signup', restaurant.restaurant_slug)
    else:
        restaurant_form = RestaurantForm(prefix="restaurant")
        address_form = AddressForm(prefix="address")
    template = 'restaurant/create.html'
    context = {"address_form": address_form, "restaurant_form": restaurant_form}
    return render(request, template, context)


def create_manager(request, restaurant_slug):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(**form.cleaned_data)
            new_user.save()
            restaurant = Restaurant.objects.get(restaurant_slug=restaurant_slug)
            Manager.objects.create(restaurant=restaurant, user=new_user)
            login(request, authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"]
            ))
            return redirect('manager_menu')
    else:
        form = UserForm()
        context = {'form': form, 'restaurant_slug': restaurant_slug}
        template = 'manager/signup.html'
        return render(request, template, context)

