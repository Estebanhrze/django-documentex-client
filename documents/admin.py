from django.contrib import admin

from .models import Document, DocumentVersion


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
