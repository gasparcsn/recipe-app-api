from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    '''Serializer for the user objects'''

    class Meta():
        model = get_user_model()
        fields = ('email', 'password', 'username', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        '''Create a new userwith encrypted password and return it'''
        return get_user_model().objects.create_user(**validated_data)


class AuthTokenSerializer(serializers.Serializer):
    '''serializer for the user authentication object'''
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
        )

    def validate(self, attributes):
        email = attributes.get('email')
        password = attributes.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attributes['user'] = user
        return attributes
