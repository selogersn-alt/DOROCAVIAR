from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage
from botocore.exceptions import ClientError

class BunnyS3Boto3Storage(S3Boto3Storage):
    """
    Stockage S3 résilient personnalisé pour BunnyCDN.
    BunnyCDN retourne parfois une erreur 403 Forbidden au lieu d'une erreur 404 Not Found
    lorsque l'on teste l'existence d'un fichier qui n'existe pas encore.
    Cette classe intercepte les erreurs 403 et 404 pour éviter de faire planter l'application.
    """
    def exists(self, name):
        try:
            return super().exists(name)
        except ClientError as e:
            if e.response['Error']['Code'] in ('404', '403'):
                return False
            raise

class BunnyS3StaticStorage(S3StaticStorage):
    """
    Stockage de fichiers statiques S3 résilient personnalisé pour BunnyCDN.
    """
    def exists(self, name):
        try:
            return super().exists(name)
        except ClientError as e:
            if e.response['Error']['Code'] in ('404', '403'):
                return False
            raise
