# from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
# from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import (
    authentication_classes,
    permission_classes
)
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from eatplusapp.models import (
    Customer,
    MenuSection,
    Item,
    Option,
    Choice,
    Restaurant,
    Order,
    OrderItem
)
from eatplusapp.serializers import (
    CustomerPlaceOrderSerializer,
    PlaceOrderItemSerializer,
    MenuSectionSerializer,
    ItemSerializer,
    OptionSerializer,
    ChoiceSerializer,
    RestarauntListSerializer,
    RestaurantSerializer,
    OrderSerializer,
    AddOrdeItemSerializer,
    OrderListSerializer,
    UpdateOrderStatusSerializer
)


@api_view(["GET"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def customer_get_restaurants(request):
    """
    List restaurants

    Return all availabilities restaurants

    Response {\n
        "restaurants": [
            {
            "id": int,
            "name": string,
            "phone": string,
            "address": int,
            "logo": url
            },
            ...
        ]
    }
    """
    restaurants = RestaurantSerializer(
        Restaurant.objects.filter(
            verified=True, available=True).order_by("-id"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"restaurants": restaurants})


@api_view(["GET"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def customer_get_items(request, restaurant_id):
    """
    Get restaurant items

    Return list of meals for restaurant

    Response {\n
        "meals": [
            {
                "id": int,
                "name": string,
                "short_description": string,
                "image": url,
                "price": int
            },
            ...
        ]
    }
    """
    items = ItemSerializer(
        Item.objects.filter(restaurant_id=restaurant_id).order_by("-id"),
        many=True,
        context={"request": request}
    ).data

    return JsonResponse({"meals": items})


@api_view(["GET"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def customer_get_menus(request, restaurant_id):
    """
    Get restaurant menus
    """
    menus = MenuSectionSerializer(
        MenuSection.objects.filter(
            restaurant_id=restaurant_id).order_by("-id"),
        many=True
    ).data

    return JsonResponse({"menus": menus})


@api_view(["GET"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def get_item_options(request, item_id):
    """
    Get item options

    Return list options of item
    """
    options = OptionSerializer(
        Option.objects.filter(item_id=item_id).order_by("-id"),
        many=True
    ).data

    return JsonResponse({"options": options})


@api_view(["GET"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def get_item_choices(request, item_id):
    """
    Get item choices

    Return list choices of item
    """
    choices = ChoiceSerializer(
        Choice.objects.filter(item_id=item_id).order_by("-id"),
        many=True
    ).data

    return JsonResponse({"choices": choices})


@api_view(["DELETE", "PUT"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def update_delete_item_choice(request, choice_id):
    """
    Update or delete item choice in order

    delete:
        Delete item choice in order

    put:
        Update item choice in order
    """
    try:
        choice = Choice.objects.get(id=choice_id)
    except Choice.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    order_items = choice.choices_orderitem.all()
    if order_items:
        orderitem = order_items[0]
        if orderitem.order.customer.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

    # update item choice
    if request.method == 'PUT':
        serializer = ChoiceSerializer(choice, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # delete item choice
    elif request.method == 'DELETE':
        choice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def customer_add_order(request):
    """
    Place order

    Request data: {\n
        'items': [
            {
                'id': int,
                'name': string,
                'price': int
            },
            ...
        ],
        'address': string,
        'restaurant_id': int,
        'payment_method_id': int
    }
    """
    order_items = PlaceOrderItemSerializer(
        request.data.get('order_items'), many=True
    ).data

    order_total = 0
    for items in order_items:
        item = Item.objects.get(id=items['item_id'])
        order_total += item.price * items['quantity']

    customer_id = Customer.objects.get(user_id=request.user.pk).id

    data = {
        'address': request.data.get('address'),
        'restaurant_id': int(request.data.get('restaurant_id')),
        'payment_method_id': int(request.data.get('payment_method_id')),
        'customer_id': customer_id,
        'total': order_total,
    }

    serializer = CustomerPlaceOrderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def add_item_to_cart(request):
    """
    Add item to Cart
    """
    customer = Customer.objects.get(user_id=request.user.pk)

    try:
        order = Order.objects.get(id=int(request.data.get('order_id')))
    except Order.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if order.customer != customer:
        return Response(status.HTTP_403_FORBIDDEN)

    serializer = AddOrdeItemSerializer(request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def orderitem_quantity_up(request, orderitem_id):
    """
    To increase quantity of items in cart
    """
    try:
        item = OrderItem.objects.get(id=orderitem_id)
    except OrderItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if item.order.customer.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    item.quantity += 1
    item.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def orderitem_quantity_down(request, orderitem_id):
    """
    To decrease quantity of items in cart
    """
    try:
        item = OrderItem.objects.get(id=orderitem_id)
    except OrderItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if item.order.customer.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if item.quantity > 0:
        item.quantity -= 1
        item.save()

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def delete_item_from_cart(request, orderitem_id):
    """
    Delete item from cart
    """
    try:
        item = OrderItem.objects.get(id=orderitem_id)
    except OrderItem.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if item.order.customer.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def customer_get_latest_order(request):
    access_token = AccessToken.objects.get(
        token=request.GET.get("access_token"),
        expires__gt=timezone.now()
    )

    customer = access_token.user.customer
    order = OrderSerializer(
        Order.objects.filter(customer=customer).last()
    ).data

    return JsonResponse({"order": order})


# RESTAURANT

@api_view(["GET"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def get_restaurant_orders(request):
    """
    Get restaurant orders

    Return orders list of restaurant

    Response {\n
        "orders": [
            {
                "id": int,
                "customer": {
                    "id": int,
                    "name": string,
                    "image": url,
                    "phone": string,
                },
                "address": string,
                "total": int,
                "sub_total": int,
                "order_for": string,
                "status": string,
                "note": string,
                "payment_method": string,
                "created_at": date,
                "picked_at": date
            },
            ...
        ]
    }
    """
    try:
        restaurant = Restaurant.objects.get(user=request.user)
    except Restaurant.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    orders = OrderListSerializer(
        Order.objects.filter(restaurant=restaurant).order_by("-id"),
        many=True
    ).data
    return JsonResponse({'orders': orders})


@api_view(["PUT"])
@authentication_classes((JSONWebTokenAuthentication, ))
@permission_classes((IsAuthenticated,))
def restaurant_update_order(request, order_id):
    """
    Update order status

    STATUS_CHOICES = (\n
        (1, "Open"),
        (2, "Placed"),
        (3, "Received"),
        (4, "Ready"),
        (5, "On the way"),
        (6, "Completed"),
        (7, "Cancelled"),
    )

    Request {\n
        "status": int
    }
    """
    try:
        restaurant = Restaurant.objects.get(user=request.user)
        order = Order.objects.get(id=order_id, restaurant=restaurant)
    except (Order.DoesNotExist, Restaurant.DoesNotExist):
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = UpdateOrderStatusSerializer(order, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def restaurant_get_latest_order(request):
    access_token = AccessToken.objects.get(
        token=request.GET.get("access_token"),
        expires__gt=timezone.now()
    )

    restaurant = access_token.user.restaurant
    order = OrderSerializer(
        Order.objects.filter(restaurant=restaurant).last()
    ).data

    return JsonResponse({"order": order})


def restaurant_order_notification(request, last_request_time):
    notification = Order.objects.filter(
        restaurant=request.user.restaurant,
        created_at__gt=last_request_time
    ).count()

    return JsonResponse({"notification": notification})


def restaurant_change_status(request):
    if request.method == "POST":
        order = Order.objects.get(
            id=request.POST["id"],
            restaurant=request.user.restaurant
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


# noinspection PyShadowingBuiltins,PyUnusedLocal
class RestaurantList(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request, format=None):
        """
        Returns a list of all restaurants in a customer's city
        """
        user = request.user
        customer = Customer.objects.filter(user_id=user.id)
        city = customer[0].city
        restaurants = Restaurant.objects.filter(city=city)
        serializer = RestarauntListSerializer(restaurants, many=True)

        return JsonResponse({"data": serializer.data})


# noinspection PyUnusedLocal,PyShadowingBuiltins
class Menu(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    query_set = Item.objects.all()

    def get(self, request, format=None):
        meals = ItemSerializer(self.query_set, many=True).data
        return JsonResponse({"meals": meals})

    @csrf_exempt
    def post(self, request, format=None):
        meals = ItemSerializer(
            Item.objects.filter(
                restaurant_id=request.restaurant_id
            ).order_by("-id"),
            many=True
        ).data

        return JsonResponse({"meals": meals})
