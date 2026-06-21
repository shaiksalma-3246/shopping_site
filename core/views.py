from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm

from .models import Product, CartItem, Order, OrderItem
from .forms import RegisterForm


def index(request):
    return render(request, 'core/index.html')


def features(request):
    return render(request, 'core/features.html')


def prices(request):
    return render(request, 'core/prices.html')


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')


def shop(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query)
        )

    if category:
        products = products.filter(category=category)

    categories = Product._meta.get_field('category').choices

    return render(
        request,
        'core/shop.html',
        {
            'products': products,
            'categories': categories,
            'selected_category': category,
            'query': query,
        }
    )


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    item.delete()

    return redirect('cart')


@login_required
def increase_quantity(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    item.quantity += 1
    item.save()

    return redirect('cart')


@login_required
def decrease_quantity(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect('cart')


@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)

    total = sum(
        (
            item.product.discount_price
            if item.product.discount_price
            else item.product.price
        ) * item.quantity
        for item in cart_items
    )

    return render(
        request,
        'core/cart.html',
        {
            'cart_items': cart_items,
            'total': total,
        }
    )


@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('shop')

    order = Order.objects.create(user=request.user)

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity
        )

    order_items = order.orderitem_set.select_related('product').all()
    order_total = sum(
        (item.product.discount_price or item.product.price) * item.quantity
        for item in order_items
    )

    cart_items.delete()

    return render(
        request,
        'core/order_confirmation.html',
        {
            'order': order,
            'order_items': order_items,
            'order_total': order_total,
        }
    )


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('orderitem_set__product')

    return render(
        request,
        'core/order_history.html',
        {
            'orders': orders,
        }
    )


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop')
    else:
        form = RegisterForm()

    return render(
        request,
        'core/register.html',
        {
            'form': form,
        }
    )


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('shop')
    else:
        form = AuthenticationForm()

    return render(
        request,
        'core/login.html',
        {
            'form': form,
        }
    )


def logout_view(request):
    logout(request)
    return redirect('index')

