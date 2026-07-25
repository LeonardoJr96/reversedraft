from datetime import date

from django.contrib.auth.password_validation import validate_password as django_validate_password


def validate_birth_date(birth_date):
    """
    Valida se a data de nascimento fornecida é válida.
    """

    MIN_AGE = 18

    today = date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    if age < MIN_AGE:
        return False
    
    return True

def validate_confirm_password(password, confirm_password):
    """
    Valida se a senha e a confirmação de senha são iguais.
    """
    return password == confirm_password

def validate_strong_password(password, *, username=None, email=None):
    """
    Roda os validadores configurados em AUTH_PASSWORD_VALIDATORS.
    Levanta django.core.exceptions.ValidationError se a senha não passar.
    """
    from user.models import User

    user_temporario = User(username=username, email=email)
    django_validate_password(password, user=user_temporario)