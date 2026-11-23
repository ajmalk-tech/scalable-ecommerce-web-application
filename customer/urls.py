from django.urls import path
from .views import *

app_name = "customer"

urlpatterns = [
    path("register/", customer_register, name="register"),
    path("login/", customer_login, name="login"),
    path("products/", customer_products, name="products"),
    path("cart/add/ajax/", ajax_addtocart, name="ajaxaddtocart"),
    path("cart/", customer_cart, name="cart"),
    path("cart/delete/ajax/", ajax_deletefromcart, name="ajaxdeletefromcart"),
    path("checkout/", customer_checkout, name="checkout"),
    path("checkout/process/ajax/", ajax_checkout, name="ajaxcheckout"),
    path(
        "checkout/success/<int:order_id>/", customer_order_success, name="ordersuccess"
    ),
    path("order/receipt/<int:order_id>/", generate_receipt_pdf, name="receipt"),
    path("logout/", customer_logout, name="logout"),
]
