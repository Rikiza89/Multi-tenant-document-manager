"""
Forms for document management.
"""
from django import forms
from .models import Document, Folder


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    file = forms.FileField(required=True)
    folder = forms.ModelChoiceField(queryset=Folder.objects.none(), required=False,
                                    widget=forms.Select(attrs={'class': 'form-input'}))
    
    class Meta:
        model = Document
        fields = ['folder', 'title', 'description', 'tags', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Document title'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'tags': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tags'}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['folder'].queryset = Folder.objects.filter(tenant=tenant)

class FolderCreateForm(forms.ModelForm):
    """Form for creating folders."""
    class Meta:
        model = Folder
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Folder name'}),
            'parent': forms.Select(attrs={'class': 'form-input'}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['parent'].queryset = Folder.objects.filter(tenant=tenant)


class DocumentSearchForm(forms.Form):
    """Form for searching documents."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 
                                     'placeholder': 'Search documents...'})
    )
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 
                                     'placeholder': 'Filter by tags'})
    )
