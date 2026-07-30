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

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("title", "description")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej. Reporte de revisión documental"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe el objetivo y hallazgos del reporte."}),
        }
