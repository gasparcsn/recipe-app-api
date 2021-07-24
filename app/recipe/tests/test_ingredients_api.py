from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    '''Test the publically available ingredients API'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that loging is required to acces this endpoint'''
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    '''Test ingredients can be retrieve by authorized users'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='passworD',
            username='dollar',
            first_name='bugg',
            last_name='roger'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        '''Test retrieving a list of ingredients'''
        Ingredient.objects.create(user=self.user, name='Pasta')
        Ingredient.objects.create(user=self.user, name='Red Sauce')

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''Test that only ingredients for authenticated user are returned'''
        user2 = get_user_model().objects.create_user(
            email='other@gmail.com',
            password='passworD1',
            username='real',
            first_name='Car',
            last_name='Montage'
        )
        Ingredient.objects.create(user=user2, name='Cashew nut')
        ingredient = Ingredient.objects.create(user=self.user, name='Yogurt')

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        '''Test creating a new ingredient'''
        payload = {'name':'Biscoit'}

        response = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        '''test creating new ingredient with invalid payload'''
        payload = {'name': ''}

        response = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
