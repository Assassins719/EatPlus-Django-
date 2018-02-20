from django import forms
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from eatplusapp.models import *
from allauth.account.forms import SignupForm


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "password", "email",)


class MemberForm(forms.ModelForm):
    email = forms.CharField(max_length=100, required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "password", "email",)


class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("username", "password")


class UserFormForEdit(forms.ModelForm):
    email = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ("address",)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['country', 'province', 'city', 'postal_code', 'street_address']


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'phone']


class RestaurantSetting(forms.ModelForm):

    class Meta:
        model = Restaurant
        exclude = ("verified", "user", "restaurant_slug")


class NewItemForm(forms.ModelForm):

    class Meta:
        model = Item
        exclude = ("restaurant", "menu_section")


class MenuSectionForm(forms.ModelForm):

    class Meta:
        model = MenuSection
        exclude = ("restaurant", "section_slug")


class OptionForm(forms.ModelForm):

    class Meta:
        model = Option
        exclude = ("item",)


class ChoiceForm(forms.ModelForm):

    class Meta:
        model = Choice
        exclude = ("option", "item", "default")


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ("note", "order_for",)


class OrderItemForm(forms.ModelForm):

    class Meta:
        model = OrderItem
        fields = ("item", "quantity",)


class ItemForm(forms.Form):

    def __init__(
            self, data=None, files=None, auto_id='id_%s', prefix=None,
            initial=None, error_class=ErrorList, label_suffix=None,
            empty_permitted=False, field_order=None,
            use_required_attribute=None, item=None
    ):
        type_of_radio = 0
        options = Option.objects.filter(item=item)

        for option in options:
            required = False
            choices = [
                (
                    _choice.id, '%s    $%s' % (
                        _choice.name, _choice.extra_charge
                    )
                )
                for _choice in Choice.objects.filter(option=option)
            ]

            widget = forms.CheckboxSelectMultiple(choices=choices)
            if option.type == type_of_radio:
                widget = forms.RadioSelect(choices=choices)
                required = True

            self.base_fields[option.name] = forms.IntegerField(
                widget=widget, required=required
            )

        super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix,
            empty_permitted, field_order, use_required_attribute
        )


class CustomerSignupForm(SignupForm):
    phone = forms.CharField(max_length=500)
    country = forms.CharField(max_length=100)
    province = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=100)
    street_address = forms.CharField(max_length=200)
    image = forms.ImageField()

    def __init__(self, *args, **kwargs):
        super(CustomerSignupForm, self).__init__(*args, **kwargs)

    def signup(self, request, user):
        address, created = Address.objects.get_or_create(
            country=self.cleaned_data['country'],
            province=self.cleaned_data['province'],
            city=self.cleaned_data['city'],
            postal_code=self.cleaned_data['postal_code'],
            street_address=self.cleaned_data['street_address']
        )
        customer = Customer.objects.create(user=user, address=address)
        customer.phone = self.cleaned_data['phone']
        customer.image = self.cleaned_data['image']
        customer.save()

    def custom_signup(self, request, user):
        self.signup(request, user)
