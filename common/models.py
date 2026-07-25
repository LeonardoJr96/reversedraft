from django.db import models
from django.conf import settings

class Status(models.TextChoices):
    OPEN = 'open', 'aberto'
    CLOSE = 'close', 'fechado'
    PROGRESS = 'progress', 'Em andamento'
    PENDING = 'pending', 'Pendente'
    PAID = 'paid', 'Pago'
    FAILED = 'failed', 'Falhou'
    EXPIRED = 'expired', 'Expirado'
    NO_WINNER = 'no_winner', 'Sem vencedor único'

class PersonalDataAccessLog(models.Model):
    """
    Registro de acesso a dados pessoais fora do Django admin
    (que já loga sozinho via LogEntry), conforme Cláusula 14.1.
    """
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,related_name='personal_data_accesses_made')
    subject = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,related_name='personal_data_accesses_received')
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)