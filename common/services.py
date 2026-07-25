from .models import PersonalDataAccessLog


def log_personal_data_access(actor, subject, action, request=None):
    ip = None
    if request is not None:
        ip = request.META.get('REMOTE_ADDR')

    PersonalDataAccessLog.objects.create(
        actor=actor, subject=subject, action=action, ip_address=ip,
    )