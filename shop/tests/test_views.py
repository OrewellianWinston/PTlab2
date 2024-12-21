from django.test import TestCase, Client
from django.urls import reverse
from shop.models import Product, Purchase, Cart
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from unittest.mock import patch
from django.contrib import messages


class TestIndexView(TestCase):
    def setUp(self):
        self.client = Client()
        self.product1 = Product.objects.create(name="Product 1", price=100)
    def test_index_view_anonymous(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/index.html')
        self.assertEqual(response.context['total_price'], 0)
    def test_index_view_authenticated(self):
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(user)
        Cart.objects.create(user=user, product=self.product1, quantity=2)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_price'], 200)

class TestPurchaseCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name="Test Product", price=100)
    def test_purchase_create_form_valid_authenticated_with_cart(self):
        self.client.force_login(self.user)
        Cart.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.post(reverse('purchase'), {'address': 'Test Address'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Purchase.objects.filter(person=self.user.username, address='Test Address').exists())
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

class TestCartView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product1 = Product.objects.create(name="Product 1", price=100)
        self.product2 = Product.objects.create(name="Product 2", price=200)
    def test_view_cart_anonymous_empty(self):
        response = self.client.get(reverse('view_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cart_items']), 0)
        self.assertEqual(response.context['total_price'], 0)
    def test_view_cart_authenticated_with_items(self):
        self.client.force_login(self.user)
        Cart.objects.create(user = self.user, product = self.product1, quantity = 2)
        Cart.objects.create(user = self.user, product = self.product2, quantity = 1)
        response = self.client.get(reverse('view_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cart_items']), 2)
        self.assertEqual(response.context['total_price'], 400)

class TestAddToCartView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name="Test Product", price=100)
    def test_add_to_cart_anonymous(self):
         response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
         self.assertEqual(response.status_code, 302)
         session_cart = self.client.session.get('cart', {})
         self.assertIn(str(self.product.id), session_cart)
    def test_add_to_cart_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cart.objects.filter(user=self.user, product=self.product).exists())


class TestRemoveFromCartView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name="Test Product", price=100)
    def test_remove_from_cart_anonymous(self):
        session = self.client.session
        session['cart'] = {str(self.product.id): {'name': 'Test Product', 'price': 100, 'quantity': 1}}
        session.save()
        response = self.client.get(reverse('remove_from_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(str(self.product.id), self.client.session.get('cart', {}))

class TestClearCartView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product1 = Product.objects.create(name="Product 1", price=100)
        self.product2 = Product.objects.create(name="Product 2", price=200)
    def test_clear_cart_anonymous(self):
        session = self.client.session
        session['cart'] = {
            str(self.product1.id): {'name': 'Product 1', 'price': 100, 'quantity': 2},
            str(self.product2.id): {'name': 'Product 2', 'price': 200, 'quantity': 1},
        }
        session.save()
        response = self.client.get(reverse('clear_cart'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get('cart'))

class TestRegistrationView(TestCase):
    def setUp(self):
        self.client = Client()

class TestLoginView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
    def test_login_post_valid(self):
        response = self.client.post(reverse('login'), {'username':'testuser', 'password':'testpassword'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

class TestProfileView(TestCase):
    def setUp(self):
         self.client = Client()
         self.user = User.objects.create_user(username='testuser', password='testpassword')
         self.product = Product.objects.create(name="Test Product", price = 100)
    def test_profile_view_authenticated_empty(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('purchases', response.context)
        self.assertEqual(len(response.context['purchases']), 0)