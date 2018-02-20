# import allauth
from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from rest_framework_jwt.views import refresh_jwt_token
from rest_framework_swagger.views import get_swagger_view

from eatplusapp import apis
from eatplusapp import manager_views
from eatplusapp import views

schema_view = get_swagger_view(title='Eatplus API')

urlpatterns = [
    url(r'^restaurants/$', views.restaurants_list, name='restaurants'),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^login/', views.MyLoginView.as_view(), name='login'),

    url(r'customer/', include([
        url(r'signup/', views.CustomerSignUpView.as_view(), name='customer_signup')
    ])),

    # manager registration
    url(r'^restaurant/create/$', manager_views.create_restaurant, name='restaurant_create'),
    url(r'^(?P<restaurant_slug>[-\w]+)/manager/signup/$', manager_views.create_manager, name='manager_signup'),

    # menus
    url(r'^(?P<restaurant_slug>[-\w]+)/pickup-menu/$',
        views.pickup_menu, name='pickup_menu'),
    url(r'^(?P<restaurant_slug>[-\w]+)/delivery-menu/$', views.delivery_menu,
        name='delivery_menu'),

    # manager
    url(r'^manager/menu/$', manager_views.menu, name='manager_menu'),

    # APIs urls
    # Docs
    url(r'^api/docs/$', schema_view),

    # Auth
    url(r'^api/auth/', include('rest_auth.urls')),
    url(r'^api/auth/registration/', include('rest_auth.registration.urls')),
    url(r'^api/refresh-token/', refresh_jwt_token),

    # Customers
    url(r'^api/v1/customer/', include([
        url(r'^restaurants/$', apis.customer_get_restaurants),
        url(r'^restaurants/(?P<restaurant_id>\d+)/menus/',
            apis.customer_get_menus),
        url(r'^restaurants/(?P<restaurant_id>\d+)/items/',
            apis.customer_get_items),
        url(r'^items/(?P<item_id>\d+)/options/', apis.get_item_options),
        url(r'^items/(?P<item_id>\d+)/choices/', apis.get_item_choices),
        url(r'^orderitems/$', apis.add_item_to_cart, name='add_item_to_cart'),
        url(r'^orderitems/(?P<orderitem_id>\d+)/$',
            apis.delete_item_from_cart),
        url(r'^orderitems/(?P<orderitem_id>\d+)/quantity-up/',
            apis.orderitem_quantity_up, name='orderitem_quantity_up'),
        url(r'^orderitems/(?P<orderitem_id>\d+)/quantity-down/',
            apis.orderitem_quantity_down, name='orderitem_quantity_down'),
        url(r'^choices/(?P<choice_id>\d+)/$',
            apis.update_delete_item_choice, name='update_delete_item_choice'),
        url(r'^orders/', apis.customer_add_order, name='customer_add_order'),
    ])),

    # Restaurants
    url(r'api/v1/restaurant/', include([
        url(r'orders/$', apis.get_restaurant_orders,
            name='get_restaurant_orders'),
        url(r'orders/(?P<order_id>\d+)/$', apis.restaurant_update_order,
            name='restaurant_update_order')    
    ])),

    # url(r'^api/restaurant/order/notification/(?P<last_request_time>.+)/$',
    #     apis.restaurant_order_notification),
    # url(r'^api/customer/order/latest/$', apis.customer_get_latest_order),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT)
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)
