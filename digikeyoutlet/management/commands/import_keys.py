import csv
from django.core.management.base import BaseCommand
from digikeyoutlet.models import Product, ProductKey  # Adjust these imports based on your actual models

class Command(BaseCommand):
    help = 'Imports keys from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to import')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        try:
            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    product_name, key = row
                    try:
                        product = Product.objects.get(name=product_name)
                        ProductKey.objects.create(product=product, key=key)
                        self.stdout.write(self.style.SUCCESS(f'Successfully imported key {key} for product {product_name}'))
                    except Product.DoesNotExist:
                        self.stderr.write(self.style.ERROR(f'Product matching query does not exist: {product_name}'))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f'Error creating ProductKey: {str(e)}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing keys: {str(e)}'))
