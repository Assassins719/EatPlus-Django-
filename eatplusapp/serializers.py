from datetime import datetime
from rest_framework import serializers

from eatplusapp.models import (
    Restaurant,
    MenuSection,
    Item,
    Option,
    Choice,
    Customer,
    Order,
    OrderItem,
    PaymentMethod
)


class RestaurantSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, restaurant):
        request = self.context.get('request')
        logo_url = restaurant.logo.url
        return request.build_absolute_uri(logo_url)

    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address", "logo")


class RestarauntListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'


class MenuSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuSection
        fields = '__all__'


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, item):
        request = self.context.get('request')
        image_url = item.image.url
        return request.build_absolute_uri(image_url)

    class Meta:
        model = Item
        fields = ("id", "name", "short_description", "image", "price")


# ORDER SERIALIZER
class OrderCustomerSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Customer
        fields = ("id", "name", "image", "phone", "address")


class OrderRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ("id", "name", "phone", "address")


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ("id", "name", "price")


class OrderItemsSerializer(serializers.ModelSerializer):
    item = OrderItemSerializer()

    class Meta:
        model = OrderItem
        fields = ("id", "item", "quantity", "sub_total")


class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    restaurant = OrderRestaurantSerializer()
    order_items = OrderItemsSerializer(many=True)
    status = serializers.ReadOnlyField(source="get_status_display")

    class Meta:
        model = Order
        fields = (
            "id", "customer", "restaurant", "order_items", "total",
            "status", "address"
        )


class OrderListSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer()
    order_for = serializers.ReadOnlyField(source="get_order_for_display")
    status = serializers.ReadOnlyField(source="get_status_display")
    payment_method = serializers.ReadOnlyField(source="payment_method.method")

    class Meta:
        model = Order
        fields = (
            "id", "customer", "address", "total", "sub_total", "order_for",
            "status", "note", "payment_method", "created_at", "picked_at"
        )


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(Order.STATUS_CHOICES)

    class Meta:
        model = Order
        fields = ("status", )

    def update(self, instance, validated_data):
        status = validated_data.get('status', instance.status)

        # if status is 'On the way' and order_for is not 'Delivery'
        if status == 5 and instance.order_for != 2:
            raise serializers.ValidationError("Wrong status.")

        instance.status = status
        instance.save()
        return instance


class PlaceOrderItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ("item_id", "quantity")


class CustomerPlaceOrderSerializer(serializers.ModelSerializer):
    address = serializers.CharField()
    restaurant_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField()
    customer_id = serializers.IntegerField()
    total = serializers.IntegerField()

    class Meta:
        model = Order
        fields = (
            "customer_id", "address", "total",
            "restaurant_id", "payment_method_id"
        )

    def create(self, validated_data):
        customer = validated_data['customer_id']

        # Check whether customer has any order that is not delivered
        if Order.objects.filter(
            customer=customer
        ).exclude(
            status=Order.COMPLETED
        ).exists():
            raise serializers.ValidationError(
                "Your last order must be completed.")

        order = Order.objects.create(
            customer_id=customer,
            restaurant_id=validated_data['restaurant_id'],
            address=validated_data['address'],
            total=validated_data['total'],
            payment_method_id=validated_data['payment_method_id']
        )

        return order


class AddOrdeItemSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer()

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ('amount', 'item', 'choice', 'total', 'id')


class CartAddSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            'items'
        )

    def create(self, validated_data):
        items = validated_data['items']

        order, created = Order.objects.get_or_create(
            user=self.context['request'].user,
        )

        for item in items:
            item = item['item']
            choice = item.get('choice')
            extra_charge = 1
            amount = item['amount']

            if amount <= 0:
                continue

            if choice:
                extra_charge = choice.extra_charge

            defaults = {
                'amount': item['amount'],
                'total': (item.price * extra_charge) * item['amount'],
                'choice': choice,
            }

            order_item, created = item.items.get_or_create(
                item=item,
                defaults=defaults
            )

            if not created:
                OrderItem.objects.filter(pk=order_item.pk).update(**defaults)

        return order


class CartRemoveItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem

    def delete(self, instance, validated_data):
        instance.delete()
        return instance


class CartUpdateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True,
    )

    class Meta:
        model = Order
        fields = ('items', 'id')

    def update(self, instance, validated_data):
        cart = instance

        items = validated_data['items']

        for item in items:
            item = item['item']
            choice = item['choice']
            choice = item.get('choice')
            amount = item['amount']

            extra_charge = 1

            if amount <= 0:
                continue

            if choice:
                extra_charge = choice.extra_charge

            defaults = {
                'amount': amount,
                'total': (item.price * extra_charge) * item['amount'],
                'item': item,
                'choice': choice,
            }

            cart.items.filter(item=item).update(**defaults)

        instance.updated = datetime.now()
        instance.save()

        return instance


class CartSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('items', 'id', 'created', 'updated')


class PaymentMethodSerializer(serializers.ModelSerializer):
    method = serializers.ReadOnlyField()

    class Meta:
        model = PaymentMethod
        fields = ('method', 'id')


class CartCheckoutSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source='customer_id')
    address = serializers.CharField()
    note = serializers.CharField(required=False)

    class Meta:
        model = Order
        fields = ('customer', 'restaurant', 'address', 'payment_method', 'note', 'id')

    def update(self, instance, validated_data):

        if not instance.items.all().exists():
            raise serializers.ValidationError('Cart is empty')

        address = validated_data['address']
        restaurant = validated_data['restaurant']
        note = validated_data.get('note')
        payment_method = validated_data.get('payment_method')
        customer = self.context['request'].user.customer

        order = Order.objects.create(
            customer=customer,
            note=note,
            restaurant=restaurant,
            address=address,
            payment_method=payment_method
        )

        for item in instance.items.all():
            order_details = order.details.create(
                restaurant=restaurant,
                item=item.item,
                quantity=item.amount,
                sub_total=item.total
            )

            if item.choice:
                order_details.choices.add(item.choice)

        instance.items.clear()

        return order
