from django.test import TestCase
from shop.models import Product, Purchase, Cart
from django.contrib.auth.models import User

class ProductModelTest(TestCase):
    def test_product_creation(self):
        product = Product.objects.create(name="Test Product", price=100)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.price, 100)
        self.assertEqual(str(product), "Test Product")

class PurchaseModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Product", price=100)
    def test_purchase_creation(self):
        purchase = Purchase.objects.create(product=self.product, person="testuser", address="Test Address")
        self.assertEqual(purchase.product, self.product)
        self.assertEqual(purchase.person, "testuser")
        self.assertEqual(purchase.address, "Test Address")
        self.assertIsNotNone(purchase.date)
        self.assertEqual(str(purchase), "Test Product purchased by testuser")

class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name="Test Product", price=100)
    def test_cart_item_creation(self):
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=2)
        self.assertEqual(cart_item.user, self.user)
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(str(cart_item), "Test Product x 2")
    def test_cart_item_total_price(self):
        cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=3)
        self.assertEqual(cart_item.total_price, 300)