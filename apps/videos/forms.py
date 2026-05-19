from django import forms
from .models import Video, Photo, Category, Comment

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'description', 'category', 'video_file', 'embed_url', 'thumbnail', 'is_short']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la vidéo'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'De quoi parle votre vidéo ?'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
            'embed_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Ou coller un lien YouTube, Vimeo, etc.'}),
            'thumbnail': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Lien vers une image miniature'}),
            'is_short': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get('video_file')
        embed_url = cleaned_data.get('embed_url')

        if not video_file and not embed_url:
            raise forms.ValidationError(
                "Veuillez soit uploader un fichier vidéo, soit fournir un lien d'intégration (YouTube/Vimeo)."
            )
        return cleaned_data

class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'image', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la photo'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Ajouter un commentaire publiques...',
                'style': 'resize: none; border-radius: 15px;'
            }),
        }
