import os
import io
import json
import razorpay
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .decorators import customer_login_required
from .models import Cart, CartItem, Order, OrderItem
from user.models import CustomerProfile
from product.models import Category, Product
from .forms import CustomerRegistrationForm, CustomerLoginForm


razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(CURRENT_DIR, "fonts", "IBMPlexMono.ttf")
BOLD_FONT_PATH = os.path.join(CURRENT_DIR, "fonts", "IBMPlexMono-Bold.ttf")
ITALIC_FONT_PATH = os.path.join(CURRENT_DIR, "fonts", "IBMPlexMono-Italic.ttf")
pdfmetrics.registerFont(TTFont("IBMPlexMono", FONT_PATH))
pdfmetrics.registerFont(TTFont("IBMPlexMono-Bold", BOLD_FONT_PATH))
pdfmetrics.registerFont(TTFont("IBMPlexMono-Italic", ITALIC_FONT_PATH))


# Create your views here.


def customer_register(request):
    if request.user.is_authenticated:
        return redirect("customer:products")

    User = get_user_model()

    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            email_id = form.cleaned_data.get("email_id")
            password = form.cleaned_data.get("password")

            try:
                user = User.objects.create_user(
                    username=username,
                    email=email_id,
                    password=password,
                    is_customer=True,
                    is_shop=False,
                )

                CustomerProfile.objects.create(user=user)

                messages.success(request, "Registration Successful")
                return redirect("customer:login")

            except Exception as e:
                print("Error:", e)
                messages.error(
                    request, "Registration failed due to system error, Try again"
                )
        else:
            messages.error(request, "Please correct the error in the form below")
    else:
        form = CustomerRegistrationForm()

    return render(request, "customer_register.html", {"form": form})


def customer_login(request):
    if request.user.is_authenticated:
        return redirect("customer:products")

    if request.method == "POST":
        form = CustomerLoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None and getattr(user, "is_customer", False):
                login(request, user)
                messages.success(request, f"Welcome {user.username}")
                return redirect("customer:products")

            elif user is not None and getattr(user, "is_shop", False):
                messages.error(request, "Enter a valid username and password")

            else:
                messages.error(request, "Invalid Username or Password")

        else:
            messages.error(request, "Please correct the input errors below")

    else:
        form = CustomerLoginForm

    return render(request, "customer_login.html", {"form": form})


def customer_products(request):
    products = (
        Product.objects.filter(stock__gt=0)
        .select_related("shop", "category")
        .order_by("category")
    )
    categories = Category.objects.all().order_by("name")

    return render(
        request,
        "customer_products.html",
        {"products": products, "categories": categories},
    )


@customer_login_required
@require_POST
def ajax_addtocart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        action = data.get("action", "set")

        try:
            quantity = int(data.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1

        if not product_id:
            return JsonResponse(
                {"status": "error", "message": "Missing product ID."}, status=400
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Product not found."}, status=404
            )

        from user.models import CustomerProfile

        customer_profile, created = CustomerProfile.objects.get_or_create(
            user=request.user
        )

        cart, created = Cart.objects.get_or_create(customer=customer_profile)

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": 1},  # if its new, starts with 1
        )

        if not item_created:
            if action == "add":
                cart_item.quantity += 1
            else:
                cart_item.quantity = quantity

        if cart_item.quantity > 20:
            cart_item.quantity = 20
        elif cart_item.quantity < 1:
            cart_item.quantity = 1

        cart_item.save()

        return JsonResponse({"status": "success", "final_quantity": cart_item.quantity})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@customer_login_required
def customer_cart(request):
    customer_profile, created = CustomerProfile.objects.get_or_create(user=request.user)

    cart = (
        Cart.objects.prefetch_related("items__product")
        .filter(customer=customer_profile)
        .first()
    )

    subtotal = 0
    cart_items = []

    if cart:
        cart_items = cart.items.all()
        for item in cart_items:
            item.total_price = item.product.price * item.quantity
            subtotal += item.total_price

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": 0 if subtotal > 500 or subtotal == 0 else 50,
        "total": subtotal + (0 if subtotal > 500 or subtotal == 0 else 50),
    }

    return render(request, "customer_cart.html", context)


@customer_login_required
def ajax_deletefromcart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")

        if not product_id:
            return JsonResponse(
                {"status": "error", "message": "Missing product ID"}, status=400
            )

        customer_profile, created = CustomerProfile.objects.get_or_create(
            user=request.user
        )
        cart = Cart.objects.filter(customer=customer_profile).first()

        if cart:
            cart_item = CartItem.objects.filter(
                cart=cart, product_id=product_id
            ).first()
            if cart_item:
                cart_item.delete()
                return JsonResponse(
                    {"status": "success", "message": "Item removed from cart"}
                )

        return JsonResponse(
            {"status": "error", "message": "Item not found in your cart"}, status=404
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@customer_login_required
def customer_checkout(request):
    customer_profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    cart = (
        Cart.objects.prefetch_related("items__product")
        .filter(customer=customer_profile)
        .first()
    )

    if not cart or not cart.items.exists():
        return redirect("customer:cart")

    subtotal = sum(item.product.price * item.quantity for item in cart.items.all())
    shipping = 0 if subtotal > 500 else 50
    total = subtotal + shipping

    amount_in_paise = int(total * 100)

    # Pre-registering a traking token layout with Razorpays test server clouds
    razorpay_order = razorpay_client.order.create(
        {"amount": amount_in_paise, "currency": "INR", "payment_capture": "1"}
    )

    context = {
        "cart_items": cart.items.all(),
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "default_address": customer_profile.delivery_address or "",
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    }
    return render(request, "customer_checkout.html", context)


@customer_login_required
def ajax_checkout(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid HTTP Method"}, status=405
        )

    try:
        data = json.loads(request.body)
        payment_method = data.get("payment_method")
        full_name = data.get("full_name")
        delivery_address = data.get("delivery_address")

        if not full_name or not delivery_address or not payment_method:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please fill out all required shipping fields.",
                },
                status=400,
            )

        # payment verification checksum gateway

        if payment_method == "Razorpay":
            # Run secure signature decryption matching algorithms to eliminate request spoofing
            params_dict = {
                "razorpay_order_id": data.get("razorpay_order_id"),
                "razorpay_payment_id": data.get("razorpay_payment_id"),
                "razorpay_signature": data.get("razorpay_signature"),
            }
            # Throws a SignatureVerificationError code automatically if validation key breaks
            razorpay_client.utility.verify_payment_signature(params_dict)
            order_status = "Processing"
        else:
            # Cash on delivery
            order_status = "Pending"

        # Accurate data snapshot log
        customer_profile = CustomerProfile.objects.get(user=request.user)
        cart = Cart.objects.filter(customer=customer_profile).first()

        if not cart or not cart.items.exists():
            return JsonResponse(
                {"status": "error", "message": "Your Shopping Cart is empty"},
                status=400,
            )

        with transaction.atomic():
            subtotal = sum(
                item.product.price * item.quantity for item in cart.items.all()
            )
            shipping = 0 if subtotal > 500 else 50
            total = subtotal + shipping

            # Save permanent master reciept details
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                delivery_address=delivery_address,
                subtotal=subtotal,
                shipping_cost=shipping,
                total_amount=total,
                status=order_status,
                payment_method=payment_method,
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity,
                )

            # cleans the temp customer checkout basket
            cart.items.all().delete()

        return JsonResponse({"status": "success", "order_id": order.id})

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse(
            {"status": "error", "message": "Cryptographic payment verification failed"},
            status=400,
        )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@customer_login_required
def customer_order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "customer_order_success.html", {"order": order})


@customer_login_required
@require_POST
def customer_logout(request):
    logout(request)

    return redirect("customer:login")


@customer_login_required
def generate_receipt_pdf(request, order_id):

    order = get_object_or_404(Order, id=order_id, user=request.user)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    left_margin = 50
    right_margin = 562  # 612 - 50 (letter width - border each side)

    # heading
    p.setFont("IBMPlexMono-Bold", 20)
    p.drawString(left_margin, 750, "Payment Receipt")

    p.setFont("IBMPlexMono", 12)
    p.drawString(left_margin, 710, f"Receipt No: {order.formatted_order_id}")
    p.drawString(left_margin, 690, f"Date: {order.created_at.strftime('%B %d, %Y')}")
    p.drawString(left_margin, 670, f"Customer Name: {order.full_name}")
    p.drawString(left_margin, 650, f"Payment Method: {order.payment_method}")

    p.drawString(
        left_margin,
        610,
        "------------------------------------------------------------------------",
    )
    y_position = 590

    p.setFont("IBMPlexMono", 12)
    for item in order.items.all():
        display_name = item.product_name
        if len(display_name) > 40:
            display_name = display_name[:35].rstrip(",. ") + " ..."

        left_text = f"{item.quantity} x {display_name}"
        right_text = f"₹{item.price * item.quantity}"

        left_width = p.stringWidth(left_text, "IBMPlexMono", 12)
        right_width = p.stringWidth(right_text, "IBMPlexMono", 12)
        available_space = (right_margin - left_margin) - left_width - right_width

        dot_width = p.stringWidth(".", "IBMPlexMono", 12)
        num_dots = int(available_space // dot_width)
        dots_string = "." * max(0, num_dots)

        p.drawString(left_margin, y_position, left_text + dots_string)
        p.drawRightString(right_margin, y_position, right_text)

        y_position -= 20

    p.drawString(
        left_margin,
        y_position,
        "------------------------------------------------------------------------",
    )
    y_position -= 20

    p.setFont("IBMPlexMono-Bold", 12)
    total_label = "Amount Paid in Total: "
    total_value = f"₹{order.total_amount}"

    label_width = p.stringWidth(total_label, "IBMPlexMono-Bold", 12)
    value_width = p.stringWidth(total_value, "IBMPlexMono-Bold", 12)
    total_space = (right_margin - left_margin) - label_width - value_width

    total_dot_width = p.stringWidth(".", "IBMPlexMono", 12)
    total_num_dots = int(total_space // total_dot_width)
    total_dot_string = "." * max(0, total_num_dots)

    p.drawString(left_margin, y_position, total_label + total_dot_string)
    p.drawRightString(right_margin, y_position, total_value)

    y_position -= 40
    p.setFont("IBMPlexMono-Italic", 10)
    p.drawString(left_margin, y_position, "Thank you for your business!")

    p.showPage()
    p.save()

    buffer.seek(0)

    filename_string = f"receipt_{order.formatted_order_id}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename_string)


def text_truncate(text, max_lenght=30):
    if len(text) > max_lenght:
        return text[: max_lenght - 3] + "..."
    return text
