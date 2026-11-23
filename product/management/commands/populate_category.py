from django.core.management.base import BaseCommand
from django.utils.text import slugify
from product.models import Category


class Command(BaseCommand):
    help = "Populates the database with default marketplace categories"
    # this one is a help message which can be accessed using [python manage.py populate_category --help]

    def handle(self, *args, **options):
        pre_categories = [
            "Processor",
            "Motherboard",
            "RAM",
            "Graphics Card",
            "Storage",
            "Power Supply",
            "PC Case",
            "Cooler",
            "Thermal Paste",
            "Keyboard",
            "Mouse",
            "Audio Devices",
        ]

        self.stdout.write(
            self.style.SUCCESS("Starting database category initialization....")
        )

        created_count = 0
        for name in pre_categories:
            # here we use get_or_create so it will prevent creating duplicate if run multiple times
            category, created = Category.objects.get_or_create(
                name=name, defaults={"slug": slugify(name)}
            )

            if created:
                created_count += 1
                self.stdout.write(f"Created category: {name}")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully added {created_count} new categories")
        )
