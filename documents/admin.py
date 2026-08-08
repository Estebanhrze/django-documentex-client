from django.contrib import admin

from .models import Document, DocumentVersion, Report


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ("number", "uploaded_by", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "uploaded_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "file")
    readonly_fields = ("created_at", "updated_at")
    inlines = (DocumentVersionInline,)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "document", "reviewed_file_name", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "description", "document__title", "reviewed_file_name", "created_by__username")
    readonly_fields = (
        "reviewed_file_path",
        "reviewed_file_name",
        "reviewed_document_updated_at",
        "created_by",
        "created_at",
    )
