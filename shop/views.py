from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import Purchase, Product
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart
# Create your views here.
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
    fields = ['person', 'address']
    template_name = 'shop/purchase_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, id=self.kwargs['product_id'])
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        form.instance.product = product
        self.object = form.save()
        return HttpResponse(f'Спасибо за покупку, {self.object.person}!')
        
    def get_success_url(self):
        return reverse_lazy('index')  # Redirect to index or any other page after purchase  


def view_cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        total_price = sum(item.total_price for item in cart_items)
    else:
        cart = request.session.get('cart', {})
        cart_items = [{'product_id': k, **v} for k, v in cart.items()]  # Format for display
        total_price = sum(item['quantity'] * item['price'] for item in cart_items)

    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            pass  
    else:
        cart = request.session.get('cart', {})
        str_product_id = str(product_id)
        if str_product_id not in cart:
            cart[str_product_id] = {'name': product.name, 'price': product.price, 'quantity': 1}
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
    return redirect('index')  # Возврат на главную

from django.shortcuts import redirect

def clear_cart(request):
    if request.user.is_authenticated:
        # Удалить все товары из корзины для аутентифицированного пользователя
        Cart.objects.filter(user=request.user).delete()
    else:
        # Очистить корзину из сессии для анонимного пользователя
        request.session['cart'] = {}
    return redirect('view_cart')  # Вернуться на страницу корзины


