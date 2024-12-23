from django.shortcuts import render, redirect, get_object_or_404 
from .models import Product, Cart, CartItem, Order, OrderItem, Product, UserProfile, Review, ProductKey
from django.conf import settings
import paypalrestsdk
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Q # Import Q for complex queries
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.mail import send_mail
import logging
from django.core.exceptions import ValidationError
from django.contrib import messages


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


def get_cart_context(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        total_cost = sum(item.product.price * item.quantity for item in cart_items)
        return {'cart_items': cart_items, 'total_cost': total_cost}
    return {'cart_items': [], 'total_cost': 0}

def home(request):
    context = get_cart_context(request)
    return render(request, 'home.html', context)


def create_payment(request, product_id):
    product = Product.objects.get(id=product_id)
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": product.name,
                    "sku": "item",
                    "price": str(product.price),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(product.price),
                "currency": "USD"
            },
            "description": product.description
        }],
        "redirect_urls": {
            "return_url": "http://localhost:8000/payment/execute/",
            "cancel_url": "http://localhost:8000/payment/cancel/"
        }
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                return redirect(approval_url)
    else:
        return render(request, 'payment/error.html', {'error': payment.error})



def execute_payment(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        return render(request, 'payment/success.html')
    else:
        return render(request, 'payment/error.html', {'error': payment.error})



@login_required
def add_to_cart(request, product_id):
    cart, created = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))  # Get quantity from POST data, default to 1 if not provided
        
        # Check if the cart item already exists
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            cart_item.quantity += quantity  # Increment quantity for existing items
        except CartItem.DoesNotExist:
            cart_item = CartItem(cart=cart, product=product, quantity=quantity)  # Create new item with the given quantity

        cart_item.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Item added to cart'})

    return redirect('view_cart')




@login_required
def update_cart(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        for item in cart.cartitem_set.all():
            quantity = int(request.POST.get(f'quantity_{item.id}', item.quantity))
            if quantity > 0:
                item.quantity = quantity
                item.save()
            else:
                item.delete()
        return redirect('view_cart')
    return redirect('view_cart')


@login_required
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        cart_item.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Item removed from cart'})

        return redirect('view_cart')
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': str(e)})
        return redirect('view_cart')




@login_required
def view_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if request.method == 'POST':
        for item in cart_items:
            if 'quantity_{}'.format(item.id) in request.POST:
                quantity = int(request.POST.get('quantity_{}'.format(item.id)))
                if quantity > 0:
                    item.quantity = quantity
                    item.save()
                else:
                    item.delete()

            if 'remove_{}'.format(item.id) in request.POST:
                item.delete()

        return redirect('view_cart')

    # Calculate the total cost for each item and the overall total cost
    for item in cart_items:
        item.total_price = item.product.price * item.quantity

    total_cost = sum(item.total_price for item in cart_items)

    context = {'cart_items': cart_items, 'total_cost': total_cost}
    context.update(get_cart_context(request))
    return render(request, 'cart.html', context)




@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = CartItem.objects.filter(cart=cart)

    if request.method == 'POST':
        if 'update' in request.POST:
            # Handle update selection
            for item in items:
                item.selected = f'selected_{item.id}' in request.POST
                item.save()
            messages.success(request, "Selection updated successfully.")
            return redirect('checkout')
        
        # Proceed with checkout
        selected_items = items.filter(selected=True)
        total_cost = sum(item.product.price * item.quantity for item in selected_items)

        if not selected_items:
            messages.error(request, "No items selected for checkout.")
            return redirect('checkout')

        # Create the order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_cost,
            order_date=timezone.now()
        )

        # Create order items
        for item in selected_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        # Assign keys to the order
        try:
            order.assign_keys()
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'checkout.html', {'items': items, 'total_cost': total_cost})

        # Clear the selected items from the cart
        selected_items.delete()

        messages.success(request, "Order completed successfully!")
        return redirect('payment_success')

    total_cost = sum(item.product.price * item.quantity for item in items if item.selected)
    context = {'items': items, 'total_cost': total_cost}
    context.update(get_cart_context(request))
    return render(request, 'checkout.html', context)

@login_required
def payment_success(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = CartItem.objects.filter(cart=cart)

    # Calculate the total amount
    total_amount = sum(item.product.price * item.quantity for item in items)

    # Create the order
    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        order_date=timezone.now()
    )

    # Create order items
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity
        )

    # Assign keys to the order
    try:
        order.assign_keys()
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('view_cart')

    # Clear the cart
    items.delete()

    return render(request, 'success.html', {'order': order})


def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        price = request.POST['price']
        description = request.POST['description']
        Product.objects.create(name=name, price=price, description=description)
        return redirect('home')
    return render(request, 'add_product.html')



def product_list(request):
    category = request.GET.get('category')
    query = request.GET.get('q')  # Get the search query
    products = Product.objects.all().order_by('name')  # Ensure the query set is ordered

    if category:
        products = products.filter(category=category)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)  # Corrected syntax here
        )

    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {'products': products}
    context.update(get_cart_context(request))
    return render(request, 'product_list.html', context)



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    purchased_keys = user_profile.purchased_keys.all()
    orders = Order.objects.filter(user=user)

    context = {'user_profile': user_profile, 'orders': orders, 'purchased_keys': purchased_keys}
    context.update(get_cart_context(request))
    return render(request, 'profile.html', context)


@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.email = request.POST['email']
        user_profile.address = request.POST['address']
        user_profile.phone = request.POST['phone']
        user.save()
        user_profile.save()
        return redirect('profile')
    return render(request, 'update_profile.html')


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    context = {'product': product, 'reviews': reviews}
    context.update(get_cart_context(request))
    return render(request, 'product_detail.html', context)


logger = logging.getLogger(__name__)

@login_required
def purchase_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    available_key = ProductKey.objects.filter(product=product, is_sold=False).first()

    if available_key:
        available_key.is_sold = True
        available_key.save()

        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.purchased_keys.add(available_key)
        user_profile.save()

        send_mail(
            'Your Product Key',
            f'Your key for {product.name} is: {available_key.key}',
            'from@example.com',
            [request.user.email],
            fail_silently=False,
        )

        return redirect('profile')

    else:
        return render(request, 'out_of_stock.html', {'product': product})


