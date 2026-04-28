from .models import AuditLog


def create_audit_log(user=None, action="", ip_address=None, user_agent="", metadata=None):
    return AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent or "",
        metadata=metadata or {},
    )