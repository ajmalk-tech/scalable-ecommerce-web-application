import os
import django
import random

# Setting up Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "silicon_bay.settings")
django.setup()

from shop.models import AvailableShopID


def populate_database():
    print("Clearing old shop IDs if any exist...")
    AvailableShopID.objects.all().delete()

    print("Generating Unique Shop IDs...")
    all_codes = [str(num) for num in range(1000, 10000)]
    random.shuffle(all_codes)

    print("Mapping entries to database objects...")
    pool_objects = [AvailableShopID(code=code) for code in all_codes]

    print("Executing bulk database insertion...")
    AvailableShopID.objects.bulk_create(pool_objects)

    print(f"Success! Total entries in database: {AvailableShopID.objects.count()}")


if __name__ == "__main__":
    populate_database()
