import re
from django import forms
from .models import Video, Photo, Category, Comment

def check_spam(text):
    if not text:
        return None
        
    # 1. Check for links to prevent bots from dropping spam sites
    url_pattern = re.compile(
        r'https?://\S+|www\.\S+|t\.me/\S+|wa\.me/\S+|viber://\S+|bit\.ly/\S+|tinyurl\.com/\S+', 
        re.IGNORECASE
    )
    if url_pattern.search(text):
        return "Les liens externes (http, https, www, telegram, whatsapp) ne sont pas autorisés afin de prévenir le spam et les publicités."
        
    # 2. Check for spam/advertising keywords (case-insensitive)
    spam_keywords = [
        r'1x\s*bet', r'mel\s*bet', r'line\s*bet', r'casino', r'crypto', r'telegram', r'whatsapp',
        r'argent\s+facile', r'rencontre\s+sexe', r'sexcam', r'webcam', r'escort', r'gagner\s+de\s+l\'argent',
        r'devenir\s+riche', r'doubler\s+votre', r'pari\s+en\s+ligne', r'paris\s+en\s+ligne', r'bet\s+en\s+ligne',
        r'sexe\s+gratuit', r'cam\s+sexe', r'sex\s+cam', r'argent\s+rapide', r'gagner\s+gros', r'investir\s+petit',
        r'gains\s+garantis', r'code\s+promo', r'promo\s+code', r'bon\s+plan\s+argent'
    ]
    
    for pattern in spam_keywords:
        if re.search(pattern, text, re.IGNORECASE):
            return "Le contenu contient des mots-clés promotionnels ou de spam interdits (paris en ligne, casino, crypto, démarchage, etc.)."
            
    return None

class VideoUploadForm(forms.ModelForm):
    website_confirm = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none !important; position:absolute; left:-9999px;',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )

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

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        spam_error = check_spam(title)
        if spam_error:
            raise forms.ValidationError(spam_error)
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        spam_error = check_spam(description)
        if spam_error:
            raise forms.ValidationError(spam_error)
        return description

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('website_confirm'):
            raise forms.ValidationError("Spam détecté.")
            
        video_file = cleaned_data.get('video_file')
        embed_url = cleaned_data.get('embed_url')

        if not video_file and not embed_url:
            raise forms.ValidationError(
                "Veuillez soit uploader un fichier vidéo, soit fournir un lien d'intégration (YouTube/Vimeo)."
            )
        return cleaned_data

class PhotoUploadForm(forms.ModelForm):
    website_confirm = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'display:none !important; position:absolute; left:-9999px;',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Photo
        fields = ['title', 'image', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la photo'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        spam_error = check_spam(title)
        if spam_error:
            raise forms.ValidationError(spam_error)
        return title

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('website_confirm'):
            raise forms.ValidationError("Spam détecté.")
        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Ajouter un commentaire publique...',
                'style': 'resize: none; border-radius: 15px;'
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        spam_error = check_spam(content)
        if spam_error:
            raise forms.ValidationError(spam_error)
        return content
