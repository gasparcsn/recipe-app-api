from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAG_URL = reverse('recipe:tag-list')


class PublicTagApiTests(TestCase):
    '''Test the publicly available api tags'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that login required for retrieving tags'''
        response = self.client.get(TAG_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    '''Test the authorized user tags api'''

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='passworD1',
            username='chester',
            first_name='chess',
            last_name='torres'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Test retrieving tags'''
        Tag.objects.create(user=self.user, name='Steaks')
        Tag.objects.create(user=self.user, name='weekend')

        response = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test that tags returned are for the authenticated user'''
        user2 = get_user_model().objects.create_user(
            email='other@gmail.com',
            password='passworD2',
            username='back',
            first_name='boll',
            last_name='pontes'
        )

        Tag.objects.create(user=user2, name='vegetables')
        tag = Tag.objects.create(user=self.user, name='dolce')

        response = self.client.get(TAG_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)

    def test_create_tag_successfull(self):
        '''Test creating a new tag'''
        payload = {'name': 'Sunday'}
        response = self.client.post(TAG_URL, payload)

        exist = Tag.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exist)

    def test_create_tag_invalid(self):
        '''test creating new tag with invalid payload'''
        payload = {'name': ''}
        response = self.client.post(TAG_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipe(self):
        '''Test by filtering tags by those assined to recipes'''
        tag1 = Tag.objects.create(user=self.user, name='Partty')
        tag2 = Tag.objects.create(user=self.user, name='birthday')
        recipe = Recipe.objects.create(
            title='Chocolate Cake',
            time_minutes=20,
            price=10.00,
            instructions='mix the chocolate with the cake',
            user=self.user
        )
        recipe.tags.add(tag1)

        response = self.client.get(TAG_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_retrieve_tags_assigned_unique(self):
        '''Test filtering tags by assigned returns unique items'''
        tag = Tag.objects.create(user=self.user, name='Partty')
        Tag.objects.create(user=self.user, name='Birthday')
        recipe1 = Recipe.objects.create(
            title='Brigadeiro',
            time_minutes=10,
            price=1.00,
            instructions='mix doce de leite with chocolate',
            user=self.user
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Candy',
            time_minutes=30,
            price=1.00,
            instructions='mix sugar with flavors',
            user=self.user
        )
        recipe2.tags.add(tag)

        response = self.client.get(TAG_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)
