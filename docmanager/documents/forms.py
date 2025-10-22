"""
Forms for document management.
"""
from django import forms
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    file = forms.FileField(required=True)
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'tags', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Document title'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 
                                                'placeholder': 'Description (optional)'}),
            'tags': forms.TextInput(attrs={'class': 'form-input', 
                                          'placeholder': 'Comma-separated tags (optional)'}),
        }


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
