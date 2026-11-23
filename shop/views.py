from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.db.models import Sum, F
from django.utils import timezone
from calendar import month_abbr
from .decorators import shop_login_required
from .models import AvailableShopID
from .forms import ShopRegistrationForm, ShopLoginForm, AddProductForm
from product.models import Product, Category
from user.models import ShopProfile
from customer.models import Order, OrderItem


# Create your views here.


def shop_register(request):
    if request.user.is_authenticated:
        return redirect("shop:register")

    User = get_user_model()

    if request.method == "POST":
        form = ShopRegistrationForm(request.POST)

        if form.is_valid():
            shop_name = form.cleaned_data.get("shop_name")
            email_id = form.cleaned_data.get("email_id")
            password = form.cleaned_data.get("password")

            try:
                with transaction.atomic():
                    target_id = AvailableShopID.objects.select_for_update().first()

                    if not target_id:
                        messages.error(request, "Registration is full.")
                        return redirect("shop:userfull")

                    unique_shop_id = target_id.code

                    user = User.objects.create_user(
                        username=unique_shop_id,
                        first_name=shop_name,
                        email=email_id,
                        password=password,
                        is_shop=True,
                        is_customer=False,
                    )

                    ShopProfile.objects.create(user=user)

                    target_id.delete()

                messages.success(
                    request,
                    f"Shop Registered Successfully!, {unique_shop_id} is your Shop ID",
                )
                return redirect("shop:login")

            except Exception as e:
                print("Error occurred:", e)
                messages.error(
                    request, "Registration failed due to system error. Try again"
                )

        else:
            messages.error(request, "Please correct the errors in the form below")

    else:
        form = ShopRegistrationForm()

    return render(request, "shop_register.html", {"form": form})


@never_cache
def shop_login(request):
    if request.user.is_authenticated:
        return redirect("shop:dashboard")

    if request.method == "POST":
        form = ShopLoginForm(request.POST)

        if form.is_valid():
            shop_id = form.cleaned_data.get("shop_id")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=shop_id, password=password)

            if user is not None and getattr(
                user, "is_shop", False
            ):  # here the false represents default value
                login(request, user)
                messages.success(request, f"Welcome {user.username}")
                return redirect("shop:dashboard")

            elif user is not None and getattr(user, "is_customer", False):
                # Block customer account from accessing the shop dashboard route
                messages.error(request, "This account is registered as a Customer!")

            else:
                messages.error(request, "Invalid Shop ID or Password")

        else:
            messages.error(request, "Please correct the input errors below")

    else:
        form = ShopLoginForm()

    return render(request, "shop_login.html", {"form": form})


@shop_login_required
def shop_dashboard(request):
    products = Product.objects.filter(shop=request.user)
    order_items = OrderItem.objects.filter(product__shop=request.user).select_related(
        "order", "product"
    )
    sales_value = F("price") * F("quantity")
    active_items = order_items.exclude(status="Cancelled")
    sales_total = active_items.aggregate(total=Sum(sales_value))["total"] or 0
    today = timezone.localdate()
    monthly_sales = []
    for offset in range(5, -1, -1):
        month_index = today.month - offset
        year = today.year + (month_index - 1) // 12
        month = (month_index - 1) % 12 + 1
        month_total = (
            active_items.filter(
                order__created_at__year=year,
                order__created_at__month=month,
            ).aggregate(total=Sum(sales_value))["total"]
            or 0
        )
        monthly_sales.append({"label": month_abbr[month], "value": float(month_total)})

    context = {
        "product_count": products.count(),
        "low_stock_count": products.filter(stock__lte=5).count(),
        "order_count": order_items.values("order_id").distinct().count(),
        "pending_count": order_items.filter(status="Pending").count(),
        "sales_total": sales_total,
        "average_order_value": (
            sales_total / active_items.values("order_id").distinct().count()
        )
        if active_items.exists()
        else 0,
        "monthly_sales": monthly_sales,
        "top_products": active_items.values("product_name")
        .annotate(units=Sum("quantity"), amount=Sum(sales_value))
        .order_by("-amount")[:5],
        "recent_orders": order_items.order_by("-order__created_at")[:6],
    }
    return render(request, "shop_dashboard.html", context)


@shop_login_required
def shop_inventory(request):
    products = (
        Product.objects.filter(shop=request.user)
        .select_related("category")
        .order_by("category")
    )
    form = AddProductForm()
    return render(request, "shop_inventory.html", {"products": products, "form": form})


@shop_login_required
def ajax_addproduct(request):
    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = request.user
            product.save()
            return JsonResponse({"status": "success", "message": "Product added!"})
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


@shop_login_required
def ajax_editproduct(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user)

    if request.method == "POST":
        # Here we overwrite the instance properties without creating a duplicate
        form = AddProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {"status": "success", "message": "Product details updated"}
            )
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=400
    )


@shop_login_required
def ajax_deleteproduct(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user)

    if request.method == "POST":
        product.delete()
        return JsonResponse(
            {"status": "success", "message": "Product removed successfully"}
        )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=400
    )


@shop_login_required
def shop_orders(request):
    order_items = (
        OrderItem.objects.filter(product__shop=request.user)
        .select_related("order", "product")
        .order_by("-order__created_at")
    )

    context = {
        "order_items": order_items,
        "pending_count": order_items.filter(order__status="Pending").count(),
        "processing_count": order_items.filter(order__status="Processing").count(),
    }
    return render(request, "shop_order.html", context)


@shop_login_required
def shop_order_update_status(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(OrderItem, id=item_id, product__shop=request.user)
        shop_click_action = request.POST.get("order_status")

        item.status = shop_click_action
        item.save()

        master_order = item.order
        all_items = master_order.items.all()

        if shop_click_action == "Shipped":
            items_still_waiting = all_items.exclude(status="Shipped")

            if items_still_waiting.exists():
                master_order.status = "Processing"
                messages.info(
                    request,
                    "Your item is marked as shipped! Overall order set to 'Processing' while awaiting remaining vendors.",
                )
            else:
                master_order.status = "Shipped"
                messages.success(
                    request,
                    f"All items have been dispatched. Order {master_order.formatted_order_id} is now SHIPPED",
                )
        elif shop_click_action == "Delivered":
            items_not_delivered = all_items.exclude(status="Delivered")
            if not items_not_delivered.exists():
                master_order.status = "Delivered"
            else:
                master_order.status = "Shipped"
        else:
            master_order.status = shop_click_action

        master_order.save()
    return redirect("shop:orders")


@shop_login_required
@require_POST
def shop_logout(request):

    # Fetching mesage and storing it into variable
    storage = messages.get_messages(request)
    storage.used = True

    # Force loop to clear it from the array
    for _ in storage:
        pass

    # logout view is given after clearing the message
    logout(request)

    return redirect("shop:login")


def shop_user_full(request):
    return render(request, "shop_user_full.html")
