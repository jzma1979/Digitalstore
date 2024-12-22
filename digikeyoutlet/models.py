from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)  # Configure this in your settings if needed

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('adguard', 'AdGuard Products'),
        ('adobe', 'Adobe Products'),
        ('aida64', 'AIDA64 Products'),
        ('aiseesoft', 'Aiseesoft Products'),
        ('aomei', 'AOMEI Products'),
        ('ashampoo', 'Ashampoo Products'),
        ('autodesk', 'Autodesk Products'),
        ('bitdefender', 'Bitdefender Products'),
        ('ccleaner', 'CCleaner Products'),
        ('corel', 'Corel Products'),
        ('drivermagician', 'DriverMagician Products'),
        ('easeus', 'EaseUS Products'),
        ('eset', 'ESET Products'),
        ('glarysoft', 'Glarysoft Products'),
        ('kaspersky', 'Kaspersky Products'),
        ('macos', 'MacOs Software'),
        ('office2013', 'Microsoft Office 2013 Products'),
        ('office2016', 'Microsoft Office 2016 Products'),
        ('office2019', 'Microsoft Office 2019 Products'),
        ('office2021', 'Microsoft Office 2021 Products'),
        ('office2024', 'Microsoft Office 2024 Products'),
        ('office365', 'Microsoft Office 365 Products'),
        ('server', 'Microsoft Server Products'),
        ('sql', 'Microsoft SQL Server Products'),
        ('visualstudio', 'Microsoft Visual Studio Products'),
        ('windows10', 'Microsoft Windows 10 Products'),
        ('windows11', 'Microsoft Windows 11 Products'),
        ('windows7', 'Microsoft Windows 7 Products'),
        ('windows8', 'Microsoft Windows 8 Products'),
        ('mindmanager', 'MindManager Products'),
        ('nitro', 'Nitro Products'),
        ('spotify', 'Spotify Subscription'),
        ('subscription', 'Subscription and Credits'),
        ('symantec', 'Symantec Products'),
        ('vmware', 'VMware Products'),
        ('vpn', 'VPN Products'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/', default='product_images/default.jpg')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='windows10')

    def __str__(self):
        return self.name

class ProductKey(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='keys')
    key = models.CharField(max_length=255, unique=True)
    is_sold = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.key} ({'sold' if self.is_sold else 'available'})"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def assign_keys(self):
        """
        Assigns available product keys to this order's items. Automatically marks keys as sold.
        """
        logger.info(f"Assigning keys for Order {self.id}...")
        try:
            order_items = self.orderitem_set.all()
            for item in order_items:
                for _ in range(item.quantity):
                    # Find the first available key for the product
                    available_key = ProductKey.objects.filter(product=item.product, is_sold=False).first()
                    if not available_key:
                        logger.error(f"No available keys for {item.product.name}!")
                        raise ValidationError(f"No available keys for {item.product.name}!")

                    # Mark the key as sold and save
                    available_key.is_sold = True
                    available_key.save()  # Ensure the update is committed to the database
                    logger.info(f"Marked key {available_key.key} as sold")

                    # Assign the key to the user's profile
                    user_profile, created = UserProfile.objects.get_or_create(user=self.user)
                    user_profile.purchased_keys.add(available_key)  # Add the key to the profile
                    user_profile.save()  # Ensure the update is committed to the database
                    logger.info(f"Added key {available_key.key} to {self.user.username}'s profile")
                    logger.info(f"User {self.user.username} now has keys: {user_profile.purchased_keys.all()}")
            logger.info(f"Finished assigning keys for Order {self.id}")
        except Exception as e:
            logger.exception("Failed to assign keys", exc_info=e)
            raise e  # Reraise the exception to be handled by the calling code if needed


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    selected = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    purchased_keys = models.ManyToManyField(ProductKey, related_name='user_profiles')

    def __str__(self):
        return self.user.username

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=1)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"

# Signal to assign keys after order is saved
@receiver(post_save, sender=Order)
def assign_keys_to_order(sender, instance, created, **kwargs):
    if created:
        instance.assign_keys()
