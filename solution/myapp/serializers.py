from myapp.models import ContactModel
from rest_framework import serializers

class ContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContactModel
        fields = [
            'id',
            'name',
            'email'
            ]
