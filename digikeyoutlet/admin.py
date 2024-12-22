from django.contrib import admin
from django.shortcuts import render
from .models import Product, ProductKey, Order, OrderItem, Cart, CartItem, UserProfile, Review

class ProductKeyInline(admin.TabularInline):
    model = ProductKey
    extra = 1  # Allows adding multiple keys at once

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    search_fields = ('name', 'category')
    list_filter = ('category',)
    inlines = [ProductKeyInline]
    actions = ['bulk_upload_keys']

    def bulk_upload_keys(self, request, queryset):
        from .forms import BulkKeyUploadForm  # Lazy import
        form = BulkKeyUploadForm()
        if 'apply' in request.POST:
            form = BulkKeyUploadForm(request.POST)
            if form.is_valid():
                keys = form.cleaned_data['keys'].splitlines()
                for product in queryset:
                    for key in keys:
                        ProductKey.objects.create(product=product, key=key)
                self.message_user(request, "Keys added successfully")
                return
        return render(request, 'admin/bulk_upload.html', {'products': queryset, 'form': form})

    bulk_upload_keys.short_description = "Bulk upload keys for selected products"

class ProductKeyAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'is_sold')
    list_filter = ('is_sold', 'product')
    search_fields = ('key',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_sold=False)  # Show only available keys

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'total_amount')
    list_filter = ('order_date',)
    search_fields = ('user__username',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'phone')
    search_fields = ('user__username', 'user__email', 'phone')

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductKey, ProductKeyAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Review)
