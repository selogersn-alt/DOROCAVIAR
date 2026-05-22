import requests
import posixpath
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible

@deconstructible
class BunnyStorage(Storage):
    """
    Stockage Django personnalisé exploitant l'API REST de BunnyCDN.
    Permet de contourner complètement les contraintes de l'API S3 de BunnyCDN
    (comme l'erreur 'S3 API is not enabled' ou les plantages liés à CreateMultipartUpload).
    """
    def __init__(self, **kwargs):
        self.api_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self.storage_zone = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        self.custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
        # Utiliser l'endpoint du CDN depuis les settings (défini par BUNNY_STORAGE_ENDPOINT dans .env)
        self.base_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', "https://storage.bunnycdn.com").rstrip('/')

    def _get_api_url(self, name):
        # Format : https://endpoint/{storage_zone}/{name}
        # S'assurer que le nom ne commence pas par un slash pour éviter de doubler les slashes
        clean_name = name.lstrip('/')
        return f"{self.base_url}/{self.storage_zone}/{clean_name}"

    def _open(self, name, mode='rb'):
        name = posixpath.normpath(name).replace('\\', '/')
        url = self._get_api_url(name)
        headers = {
            "AccessKey": self.api_key
        }
        # Téléchargement par streaming pour économiser la mémoire
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        if response.status_code == 200:
            return ContentFile(response.content)
        raise FileNotFoundError(f"Fichier introuvable sur BunnyCDN : {name} (Status: {response.status_code})")

    def _save(self, name, content):
        name = posixpath.normpath(name).replace('\\', '/')
        url = self._get_api_url(name)
        
        headers = {
            "AccessKey": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        # Repositionner le pointeur de fichier
        content.seek(0)
        
        # Téléversement en streaming HTTP PUT direct
        # timeout=1200 secondes (20 minutes) pour tolérer de très grosses vidéos
        response = requests.put(url, data=content, headers=headers, timeout=1200)
        
        if response.status_code not in (200, 201):
            raise IOError(f"Échec de l'upload sur BunnyCDN : {response.status_code} {response.text}")
            
        return name

    def exists(self, name):
        name = posixpath.normpath(name).replace('\\', '/')
        url = self._get_api_url(name)
        headers = {
            "AccessKey": self.api_key
        }
        try:
            # HEAD request rapide pour tester l'existence sur BunnyCDN Storage
            response = requests.head(url, headers=headers, timeout=15)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def delete(self, name):
        name = posixpath.normpath(name).replace('\\', '/')
        url = self._get_api_url(name)
        headers = {
            "AccessKey": self.api_key
        }
        try:
            requests.delete(url, headers=headers, timeout=15)
        except requests.RequestException:
            pass

    def url(self, name):
        name = posixpath.normpath(name).replace('\\', '/').lstrip('/')
        # Renvoie l'URL publique délivrée par le CDN
        return f"https://{self.custom_domain}/{name}"

# Conserver les anciennes classes vides pour éviter des plantages de migration Django si elles sont référencées.
class BunnyS3Boto3Storage(BunnyStorage):
    pass

class BunnyS3StaticStorage(Storage):
    pass
