# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
        self.assertEqual(found_product.available, product.available)
        self.assertEqual(found_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Change fields
        product.description = "New description"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "New description")
        # Fetch it back
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "New description")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # Delete it
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find Products by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_update_with_no_id(self):
        """It should raise DataValidationError when updating with no id"""
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_serialize_product(self):
        """It should Serialize a Product"""
        product = ProductFactory()
        data = product.serialize()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(data["price"], str(product.price))
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    def test_deserialize_product(self):
        """It should Deserialize a Product"""
        data = ProductFactory().serialize()
        product = Product()
        product.deserialize(data)
        self.assertEqual(product.name, data["name"])
        self.assertEqual(product.description, data["description"])
        self.assertEqual(product.price, Decimal(data["price"]))
        self.assertEqual(product.available, data["available"])
        self.assertEqual(product.category.name, data["category"])

    def test_deserialize_bad_data(self):
        """It should not Deserialize bad data"""
        product = Product()

        # Test non-dictionary data
        data = "this is not a dictionary"
        self.assertRaises(DataValidationError, product.deserialize, data)

        # Test missing required fields
        data = {"name": "Test", "price": "bad_price"}
        self.assertRaises(DataValidationError, product.deserialize, data)

        # Test invalid category
        invalid_category_data = {
            "name": "Test",
            "description": "Test description",
            "price": "10.50",
            "available": True,
            "category": "INVALID_CATEGORY"  # Несуществующая категория
        }
        self.assertRaises(DataValidationError, product.deserialize, invalid_category_data)

        # Test data is a list (not a dict)
        invalid_data_list = [{"name": "Test"}]
        self.assertRaises(DataValidationError, product.deserialize, invalid_data_list)

    def test_find_by_price_string(self):
        """It should Find Products by Price passed as string"""
        products = ProductFactory.create_batch(3)
        expected_price = Decimal("99.99")
        products[0].price = expected_price
        for product in products:
            product.create()

        found = Product.find_by_price(' "99.99" ')
        self.assertEqual(found.count(), 1)
        self.assertEqual(found[0].price, expected_price)

    def test_find_by_price(self):
        """It should Find Products by Price"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        price = products[0].price
        count = len([p for p in products if p.price == price])
        found = Product.find_by_price(price)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.price, price)

    def test_create_product_with_max_length(self):
        """It should Create Product with Max Length Fields"""
        product = ProductFactory(
            name="X" * 100,
            description="D" * 250
        )
        product.create()
        self.assertIsNotNone(product.id)
        found = Product.find(product.id)
        self.assertEqual(found.name, "X" * 100)
        self.assertEqual(found.description, "D" * 250)

    def test_update_no_id(self):
        """It should Raise Error When Updating With No ID"""
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_string_representation(self):
        """It should Return Correct String Representation"""
        product = ProductFactory()
        self.assertEqual(
            str(product),
            f"<Product {product.name} id=[{product.id}]>"
        )

    def test_price_special_cases(self):
        """It should Handle Decimal Price Cases"""
        product = ProductFactory(price=Decimal("99999999.99"))
        product.create()
        found = Product.find(product.id)
        self.assertEqual(found.price, Decimal("99999999.99"))

        product = ProductFactory(price=Decimal("0.01"))
        product.create()
        found = Product.find(product.id)
        self.assertEqual(found.price, Decimal("0.01"))

    def test_init_db(self):
        """It should Initialize the Database"""
        Product.init_db(app)
        self.assertIsNotNone(db.session)
