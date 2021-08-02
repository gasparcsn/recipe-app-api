from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='test@gmail.com', password='passworD'):
    '''create a sample user'''
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_succesfull(self):
        '''Test creating a new user with email is succesfull'''

        email = 'test@gmail.com'
        password = 'Password123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_nomalized(self):
        '''Test the email for a new user is normalized'''
        email = 'test@GMAIL.COM'
        user = get_user_model().objects.create_user(email, 'Password123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        '''Test creating user with no email raises error'''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123455678')

    def test_create_superuser(self):
        '''Test creating a new superuser'''
        user = get_user_model().objects.create_superuser(
            'test@gmail.com',
            'Pass123456789'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        '''Test the tag string representation'''
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Steak'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        '''test the ingredient string representation'''
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Pepper'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        '''test the recipe string representation'''
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Chicken with Pasta',
            time_minutes=5,
            price=5.00,
            instructions='prepare the pasta first, add the chicken... \
                            That is finished.'
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        '''Test that image is saved in the correct location'''
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        expected_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, expected_path)
