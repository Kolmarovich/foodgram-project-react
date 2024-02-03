import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Имя пользователя <me> недопустимо.')
    if not re.match(r'^[\w.@+-]+$', value):
        raise ValidationError(
            f'Недопустимые символы <{value}> в имени пользователя.')
