from django.urls import path
from .views import *

app_name = "shop"

urlpatterns = [
    path("register/", shop_register, name="register"),
    path("login/", shop_login, name="login"),
    path("dashboard/", shop_dashboard, name="dashboard"),
    path("inventory/", shop_inventory, name="inventory"),
    path("inventory/add/ajax/", ajax_addproduct, name="addproduct"),
    path("inventory/edit/ajax/<int:product_id>/", ajax_editproduct, name="editproduct"),
    path(
        "inventory/delete/ajax/<int:product_id>/",
        ajax_deleteproduct,
        name="deleteproduct",
    ),
    path("orders/", shop_orders, name="orders"),
    path("items/update/<int:item_id>", shop_order_update_status, name="update_status"),
    path("full/", shop_user_full, name="userfull"),
    path("logout/", shop_logout, name="logout"),
]
