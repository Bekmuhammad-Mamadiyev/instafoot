from rest_framework.exceptions import ValidationError

from shared.utility import check_email_or_phone, send_email
from users.models import User, UserConfirmation, VIA_PHONE, VIA_EMAIL, NEW, CODE_VERIFIED, DONE
from rest_framework import serializers
from django.db.models import Q



class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status'
        )
        extra_kwargs = {
            'auth_type': {'read_only': True, 'required': False},
            'auth_status': {'read_only': True, 'required': False}
        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
            # send_phone_code(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        print(data)
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)
        if input_type == "email":
            data = {
                "email": user_input,
                "auth_type": VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                "phone_number": user_input,
                "auth_type": VIA_PHONE
            }
        else:
            data = {
                'success': False,
                'message': "You must send email or phone number"
            }
            raise ValidationError(data)

        return data
    def validate_phone_and_email(self,value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            raise ValidationError({"success":False,
                                   "message": "Email already exists"})
        elif value and User.objects.filter(phone_number=value).exists():
            raise ValidationError({"success":False,
                                   "message": "Phone number already exists"})
        return value

    def to_representation(self, instance):
        print("torepresentation:",instance)

        data = super(SignUpSerializer,self).to_representation(instance)
        data.update(instance.token())

        return data
