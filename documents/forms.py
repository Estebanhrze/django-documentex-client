from django import forms

from .models import Document, DocumentVersion, Report


class RemoteFileValidationMixin:
    max_upload_size = 10 * 1024 * 1024

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if uploaded_file is None:
            return uploaded_file
        if uploaded_file.size > self.max_upload_size:
            raise forms.ValidationError("El archivo no puede superar los 10 MB.")
        return uploaded_file


class DocumentForm(RemoteFileValidationMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ("title", "file", "status")
        widgets = {"title": forms.TextInput(attrs={"placeholder": "Ej. Contrato de prestación de servicios"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar, el archivo es opcional; el existente se conserva si no se envía otro.
        if self.instance and self.instance.pk:
            self.fields["file"].required = False
        else:
            self.fields["file"].required = True


class DocumentVersionForm(RemoteFileValidationMixin, forms.ModelForm):
    class Meta:
        model = DocumentVersion
        fields = ("file",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True

class DocumentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.title} — {obj.filename}"


class ReportForm(forms.ModelForm):
    document = DocumentChoiceField(
        queryset=Document.objects.none(),
        label="Documento a revisar",
        empty_label="Selecciona un documento",
    )

    class Meta:
        model = Report
        fields = ("document", "title", "description")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej. Reporte de revisión documental"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe el objetivo y hallazgos del reporte."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].queryset = Document.objects.order_by("title")

    def clean_document(self):
        document = self.cleaned_data["document"]
        if not document.file_path and not document.file:
            raise forms.ValidationError("El documento seleccionado no tiene un archivo disponible.")
        return document
