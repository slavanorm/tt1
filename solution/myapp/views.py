from myapp.models import ContactModel
from myapp import settings
from myapp.serializers import (
    ContactSerializer,
)
from django.core.mail import send_mail
from rest_framework import permissions, viewsets

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    queryset = ContactModel.objects.all()
    permission_classes = [permissions.DjangoModelPermissions]

    def destroy(self, request, *args, **kwargs):
        # todo: cleanup from .env
        # todo: restore gmail protection
        instance = self.get_object()
        send_mail(
            'deletion notification',
            'notificiation on deletion of '+ ','.join(
                str(getattr(instance,e.name)) for e in instance._meta.fields),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.NOTIFICATION_TARGET],
            auth_user=settings.EMAIL_HOST_USER,
            auth_password=settings.EMAIL_HOST_PASSWORD,
            )
        return super().destroy(request,*args)