from django import forms

from .models import Document, DocumentVersion


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("title", "file", "status")
        widgets = {"title": forms.TextInput(attrs={"placeholder": "Ej. Contrato de prestación de servicios"})}

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("El archivo no puede superar los 10 MB.")
        return uploaded_file


class DocumentVersionForm(forms.ModelForm):
    class Meta:
        model = DocumentVersion
        fields = ("file",)

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("El archivo no puede superar los 10 MB.")
        return uploaded_file
