from django import forms
from .models import Photo, Video, Location, MediaType

class MediaUploadForm(forms.Form):
    category = forms.ChoiceField(
        choices=[(loc.name, loc.value) for loc in Location], 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    media_type = forms.ChoiceField(
        choices=[(mt.name, mt.value) for mt in MediaType], 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    upload_method = forms.ChoiceField(
        choices=[('file', 'Upload Files from PC'), ('url', 'Upload from URL')],
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'upload-method-radio'})
    )
    media_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter image or video URL'})
    )

    def clean(self):
        cleaned_data = super().clean()
        upload_method = cleaned_data.get('upload_method')
        media_url = cleaned_data.get('media_url')

        if upload_method == 'url':
            if not media_url:
                raise forms.ValidationError("Please provide a URL.")

        return cleaned_data
