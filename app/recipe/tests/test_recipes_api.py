from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    '''Return recipe detail URL'''
    return reverse('recipe:recipe-detail', args=[recipe_id])

def sample_tag(user, name='Main course'):
    '''Create and return a sample tag'''
    return Tag.objects.create(user=user, name=name)

def sample_ingredient(user, name='water'):
    '''Create and return a sample ingredient'''
    return Ingredient.objects.create(user=user, name=name)

def sample_recipe(user, **params):
    '''Create and return a sample recipe'''
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
        'instructions': 'do the intructions'
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    '''Test unauthenticated recipe API access'''

    def setUp(self):
        self.client = APIClient()

    def test_recipes_required_auth(self):
        '''Test the authentication is required'''
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    '''Test authenticated recipe API access'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test123@gmail.com',
            password='Pass123',
            username='Cachorro',
            first_name='carro',
            last_name='water'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving list of recipe'''
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipe = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):
        '''Test retrieving recipes for user'''
        user2 = get_user_model().objects.create_user(
            email='user2@gmail.com',
            password='Pass1234',
            username='guitar',
            first_name='cords',
            last_name='glasses'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        '''Test viewing a recipe detail'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        '''Testing creating recipe'''
        payload = {
            'title': 'Macarone',
            'time_minutes': 5,
            'price': 20.00,
            'instructions': 'ferve in water and do the sauce, then mix all tgr'
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        '''Test creating a recipe with tags'''
        tag1 = sample_tag(user=self.user, name='friends')
        tag2 = sample_tag(user=self.user, name='saturday')
        payload = {
            'title': 'Parmegiana',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 25,
            'price': 100.00,
            'instructions': 'steak + cheese + reed sauce = parmegiana'
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        tag = recipe.tags.all()
        self.assertEqual(tag.count(), 2)
        self.assertIn(tag1, tag)
        self.assertIn(tag2, tag)

    def test_create_recipe_with_ingredients(self):
        '''Test creating a recipe with ingredients'''
        ingredient1 = sample_ingredient(user=self.user, name='Apple')
        ingredient2 = sample_ingredient(user=self.user, name='Sugar')
        payload = {
            'title': 'Apple Suit',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 30,
            'price': 2.00,
            'instructions': 'Throw the sugar broth on top of the apple'
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredient = recipe.ingredients.all()
        self.assertEqual(ingredient.count(), 2)
        self.assertIn(ingredient1, ingredient)
        self.assertIn(ingredient2, ingredient)

    def test_parcial_update_recipe(self):
        '''Test updating a recipe with patch'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        new_tag = sample_tag(user=self.user, name='Pepper')

        payload = {'title': 'Natchos', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], new_tag)
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 1)

    def test_full_update_recipe(self):
        '''Test updating a recipe with put'''

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        payload = {
            'title': 'Marshmellow suit',
            'time_minutes': 40,
            'price': 5.00,
            'instructions': 'marshmellow bolls...'
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.instructions, payload['instructions'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 0)
