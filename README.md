# Silicon Bay

Silicon Bay is a Django multi-vendor marketplace for computer hardware.
Customers can browse products, manage a cart, and place orders.
Shops can register, manage their inventory, and view and update orders.

## Features

- Customer registration and login
- Shop registration with a generated four-digit Shop ID
- Product catalog with category filtering
- Shopping cart and checkout
- Cash on delivery and Razorpay payment options
- Order history and downloadable PDF receipts
- Shop inventory management and order status updates
- Shop dashboard with sales and inventory summaries

## Built with

- Python 3.12–3.14
- Django 6.0.7
- SQLite for local development
- Razorpay for online payments
- Pillow for product image handling
- ReportLab for PDF receipt

## Requirements

- Python 3.12, 3.13, or 3.14
- Git
- Razorpay API credentials to use Razorpay checkout

## Setup on Windows

Open Command Prompt in the project directory — the directory containing `manage.py` — then run:

```
cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Set the required environment variables in the same Command Prompt window. Replace the example values with your own development credentials:

```
cmd
set DJANGO_SECRET_KEY=replace-with-a-long-random-secret
set RAZORPAY_KEY_ID=your-razorpay-key-id
set RAZORPAY_KEY_SECRET=your-razorpay-key-secret
```

These values are only set for the current Command Prompt session. Set them again in a new window before running the project.

## Initialize the database

Apply the database migrations:

```
cmd
python manage.py migrate
```

Add the default product categories:

```
cmd
python manage.py populate_category
```

Generate the pool of shop registration IDs:

```
cmd
python populate.py
```

Create an administrator account if you want to use the Django admin site:

```
cmd
python manage.py createsuperuser
```

## Run locally

```
cmd
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

Customer registration and login are at [`/register/`](http://127.0.0.1:8000/register/) and [`/login/`](http://127.0.0.1:8000/login/).
Shop registration and login are at [`/shop/register/`](http://127.0.0.1:8000/shop/register/) and [`/shop/login/`](http://127.0.0.1:8000/shop/login/).
The Django admin site is at [`/admin/`](http://127.0.0.1:8000/admin/).

## Project structure

- `customer/` — customer accounts, carts, checkout, orders, and receipts
- `shop/` — shop accounts, inventory, dashboards, and order management
- `product/` — products, categories, and category setup command
- `user/` — custom user model and customer/shop profiles
- `templates/` — customer and shop HTML templates
- `static/` — CSS assets
- `media/` — uploaded product and profile images
- `silicon_bay/` — Django project settings and URL configuration

## Notes

- The local SQLite database is created as `db.sqlite3` after migrations. It is not included in the repository.
- Uploaded media files are not included in the repository. A fresh local database will not contain the existing sample products or their images.
- The project requires `DJANGO_SECRET_KEY`, `RAZORPAY_KEY_ID`, and `RAZORPAY_KEY_SECRET` to be set before Django starts.
- Do not commit real API credentials, `.env` files containing secrets, customer data, or production database files.
- `DEBUG` is enabled in the current settings for development. Review the Django deployment checklist and configure production settings before deploying publicly.
