from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')

TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''Test the users API (public)'''

    def set_up(self):
        self.client = APIClient()

    def test_create_user_valid_success(self):
        '''Test creating using with a valid payload is successfull'''

        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'username': 'name',
            'first_name': 'test',
            'last_name': 'case',
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
        '''Test creating a user that already exists fails'''
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpassworD',
            'username': 'name',
            'first_name': 'test',
            'last_name': 'case',
        }
        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''Test that password must be more than 5 charactes'''
        payload = {
            'email': 'test@gmail.com',
            'password': 'test',
            'username': 'name',
            'first_name': 'test',
            'last_name': 'case',
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''Test that a token was created for the user'''
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpassworD',
            'username': 'testuser',
            'first_name': 'test',
            'last_name': 'case',
            }

        create_user(**payload)
        response = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credential(self):
        '''test that tokes is not create if invalid credentials are given'''
        create_user(email='test@gmail.com', password='testpassword', username='testuser', first_name='test', last_name='case')
        payload = {
            'email': 'test@gmail.com',
            'password': 'wrong',
            'username': 'testuser',
            'first_name': 'test',
            'last_name': 'case',
            }

        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        '''Test that token is not created if the user does not exist'''
        payload = {
            'email': 'test',
            'password': 'testpassworD',
            'username': 'testuser',
            'first_name': 'test',
            'last_name': 'case',
            }

        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        '''Test that email and password are required'''
        payload = {
            'email': 'test',
            'password': '',
            'username': 'testuser',
            'first_name': 'test',
            'last_name': 'case',
            }

        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
