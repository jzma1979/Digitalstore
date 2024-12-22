from django import forms
from .models import ProductKey

class BulkKeyUploadForm(forms.Form):
    keys = forms.CharField(widget=forms.Textarea, help_text="Enter one key per line")
