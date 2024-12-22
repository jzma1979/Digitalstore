import csv
import os
import django

print("Setting up Django environment...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitalstore.settings')

print("Django settings module: ", os.environ.get('DJANGO_SETTINGS_MODULE'))
django.setup()

from digikeyoutlet.models import Product, ProductKey

def bulk_add_keys(file_path):
    abs_path = os.path.abspath(file_path)
    print(f"Loading keys from: {abs_path}")
    with open(abs_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            product_name = row['product_name']
            key = row['key']
            try:
                product = Product.objects.get(name=product_name)
                ProductKey.objects.create(product=product, key=key)
                print(f"Successfully added key {key} for product {product_name}")
            except Product.DoesNotExist:
                print(f"Product {product_name} does not exist. Skipping key {key}")

# Example usage
bulk_add_keys('data/product_keys.csv')


