from django.db import models
from django.db.models import Q, CheckConstraint
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, null=False, unique=True)
    cellphone = models.CharField(max_length=14)
    address = models.CharField(max_length=255)
    town = models.CharField(max_length=45)
    post_code = models.CharField(max_length=45)
    country = models.CharField(max_length=45)
    lance_credits = models.IntegerField(default=0)
    birth_date = models.DateField()
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    self_excluded_until = models.DateTimeField(null=True, blank=True)

    REQUIRED_FIELDS = ['email', 'cpf', 'cellphone', 'address', 'town', 'post_code', 'country', 'birth_date']
    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(lance_credits__gte=0),
                name='lance_credits_nao_negativo'
            )
        ]

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auction = models.ForeignKey('auction.Auction', on_delete=models.CASCADE)