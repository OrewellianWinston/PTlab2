from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import Purchase, Product, Cart
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import RegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.decorators import method_decorator


def index(request):
    products = Product.objects.all()
    if request.user.is_authenticated:
        # Если пользователь аутентифицирован, считаем стоимость корзины из базы
        cart_items = Cart.objects.filter(user=request.user)
        total_price = sum(item.total_price for item in cart_items)
    else:
        # Для анонимных пользователей считаем корзину из сессии
        cart = request.session.get('cart', {})
        total_price = sum(item['quantity'] * item['price'] for item in cart.values())

    context = {
        'products': products,
        'total_price': total_price,
    }
    return render(request, 'shop/index.html', context)


class PurchaseCreate(CreateView):
    model = Purchase
    fields = ['address']  # Removed person, since we assume person is the user
    template_name = 'shop/purchase_form.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Пожалуйста, войдите в аккаунт или зарегистрируйтесь.")
            return redirect('login')
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
             cart_items = Cart.objects.filter(user=self.request.user).select_related('product')
             formatted_cart_items = [{
                 'product_id': item.product.id,
                 'name': item.product.name,
                 'price': item.product.price,
                 'quantity': item.quantity
             } for item in cart_items]
             total_price = sum(item.total_price for item in cart_items)
        else:
            cart = self.request.session.get('cart', {})
            formatted_cart_items = [{'product_id': k, **v} for k, v in cart.items()]  # Format for display
            total_price = sum(item['quantity'] * item['price'] for item in formatted_cart_items)
        context['cart_items'] = formatted_cart_items
        context['total_price'] = total_price
        return context

    @transaction.atomic
    def form_valid(self, form):

        if self.request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=self.request.user)
        else:
            cart = self.request.session.get('cart', {})
            cart_items = [{'product_id': k, **v} for k, v in cart.items()]

        if not cart_items:
            return HttpResponse('Cart is empty')

        for item in cart_items:
            if self.request.user.is_authenticated:
                purchase_product = item.product
                quantity = item.quantity
                Purchase.objects.create(product=purchase_product, person=self.request.user.username,
                                        address=form.cleaned_data['address'])
            else:
                purchase_product = Product.objects.get(id=item['product_id'])
                quantity = item['quantity']
                Purchase.objects.create(product=purchase_product, person='Anonymous',
                                        address=form.cleaned_data['address'])

        if self.request.user.is_authenticated:
            Cart.objects.filter(user=self.request.user).delete()
        else:
            self.request.session['cart'] = {}

        messages.success(self.request, "Вы оплатили, возвращаемся на главную страницу.")

        return redirect('index')


def view_cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).select_related('product')
        formatted_cart_items = [{
            'product_id': item.product.id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity
        } for item in cart_items]
        total_price = sum(item.total_price for item in cart_items)
    else:
        cart = request.session.get('cart', {})
        formatted_cart_items = [{'product_id': k, **v} for k, v in cart.items()]  # Format for display
        total_price = sum(item['quantity'] * item['price'] for item in formatted_cart_items)

    return render(request, 'shop/cart.html', {'cart_items': formatted_cart_items, 'total_price': total_price})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product, defaults={'quantity': 1})
        if not created:
             messages.error(request, "В корзине уже есть этот товар.")
    else:
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
             messages.error(request, "В корзине уже есть этот товар.")
        else:
            cart[str(product_id)] = {'name': product.name, 'price': product.price, 'quantity': 1}
        request.session['cart'] = cart
    return redirect('index')

def remove_from_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        Cart.objects.filter(user=request.user, product=product).delete()
    else:
        cart = request.session.get('cart', {})
        str_product_id = str(product_id)
        if str_product_id in cart:
            del cart[str_product_id]
        request.session['cart'] = cart
    return redirect('view_cart')


def clear_cart(request):
    if request.user.is_authenticated:
        # Удалить все товары из корзины для аутентифицированного пользователя
        Cart.objects.filter(user=request.user).delete()
    else:
        # Очистить корзину из сессии для анонимного пользователя
        request.session['cart'] = {}
    return redirect('view_cart')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegistrationForm()
    return render(request, 'shop/register.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'shop/login.html')


def logout_user(request):
    logout(request)
    return redirect('index')


@login_required
def profile(request):
    purchases = Purchase.objects.filter(person=request.user.username).order_by('-date')
    return render(request, 'shop/profile.html', {'purchases': purchases})