from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate


ROLE_PERMISSIONS = {
    "Editor documental": {
        "view_document",
        "add_document",
        "change_document",
        "delete_document",
        "view_documentversion",
        "add_documentversion",
        "change_documentversion",
        "delete_documentversion",
        "view_reports",
        "view_report",
        "add_report",
    },
    "Revisor documental": {
        "view_document",
        "view_documentversion",
        "view_reports",
        "view_report",
        "add_report",
    },
}


def ensure_document_roles(sender, using, **kwargs):
    """Create/update the document roles after Django creates permissions."""
    permissions = Permission.objects.using(using).filter(
        content_type__app_label="documents",
        codename__in=set().union(*ROLE_PERMISSIONS.values()),
    )
    by_codename = {permission.codename: permission for permission in permissions}

    for group_name, codenames in ROLE_PERMISSIONS.items():
        if not codenames.issubset(by_codename):
            # Django will retry this handler after the next migrate command.
            continue
        group, _ = Group.objects.using(using).get_or_create(name=group_name)
        group.permissions.set([by_codename[codename] for codename in codenames])


def register_role_signal(app_config):
    post_migrate.connect(
        ensure_document_roles,
        sender=app_config,
        dispatch_uid="documents.ensure_document_roles",
    )