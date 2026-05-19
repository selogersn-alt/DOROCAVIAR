from celery import shared_task
from django.utils import timezone
from .models import ImportSource
from .importers import APIImporter, ScrapingImporter

@shared_task
def run_all_active_imports():
    """Tâche planifiée pour exécuter tous les imports actifs."""
    sources = ImportSource.objects.filter(is_active=True)
    for source in sources:
        # Exécute chaque import dans une tâche séparée (asynchrone)
        process_import_source.delay(source.id)
    return f"Triggered {sources.count()} import sources."

@shared_task
def process_import_source(source_id):
    """Exécute l'importation pour une source spécifique."""
    try:
        source = ImportSource.objects.get(id=source_id)
    except ImportSource.DoesNotExist:
        return f"Source {source_id} introuvable."
        
    print(f"Démarrage de l'import pour: {source.name}")
    
    # Sélection de la stratégie d'import
    if source.source_type == 'API':
        importer = APIImporter(source)
    elif source.source_type == 'SCRAPE':
        importer = ScrapingImporter(source)
    else:
        return "Type de source inconnu."
        
    # Exécution de l'importeur qui va créer les vidéos en évitant les doublons
    stats = importer.run()
    
    # Mise à jour de la date de dernier import
    source.last_run = timezone.now()
    source.save()
    
    return f"Import terminé pour {source.name}: {stats}"

@shared_task
def process_uploaded_video_task(video_id):
    """
    Tâche Celery pour compresser une vidéo en H.264 et extraire une miniature en tâche de fond.
    Fonctionne de manière transparente en local ou avec un stockage distant (S3/Bunny).
    """
    import os
    import tempfile
    import subprocess
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from apps.videos.models import Video

    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return f"Vidéo {video_id} introuvable."

    if not video.video_file:
        return "Aucun fichier vidéo associé."

    print(f"Début du traitement de la vidéo : {video.title} (ID: {video_id})")

    # 1. Obtenir le fichier local ou le télécharger temporairement
    temp_input = None
    input_path = None

    try:
        input_path = video.video_file.path
    except (NotImplementedError, AttributeError):
        # Stockage distant (BunnyCDN, S3) : on télécharge localement
        temp_input = tempfile.NamedTemporaryFile(suffix=os.path.splitext(video.video_file.name)[1], delete=False)
        try:
            video.video_file.open('rb')
            for chunk in video.video_file.chunks():
                temp_input.write(chunk)
            temp_input.flush()
            input_path = temp_input.name
        finally:
            video.video_file.close()

    # Définir les fichiers de sortie temporaires
    temp_output_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_output_video.close()
    compressed_path = temp_output_video.name

    temp_output_thumb = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    temp_output_thumb.close()
    thumb_path = temp_output_thumb.name

    try:
        # 2. Lancement de la compression FFMPEG (vcodec libx264, preset fast, crf 28)
        print(f"Compression vidéo en cours pour {video.title}...")
        compress_cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vcodec', 'libx264', '-crf', '28', '-preset', 'fast',
            '-acodec', 'aac', '-movflags', '+faststart',
            compressed_path
        ]
        
        # Exécuter et capturer le retour
        process = subprocess.run(compress_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            print(f"Erreur de compression FFMPEG : {process.stderr.decode('utf-8', errors='ignore')}")
            # Si la compression échoue, on conserve le fichier initial
            compressed_path = input_path
        else:
            print("Compression vidéo réussie !")

        # 3. Extraction automatique de miniature si nécessaire
        extracted_thumb = False
        if not video.thumbnail and not video.thumbnail_file:
            print(f"Génération de la miniature automatique pour {video.title}...")
            thumb_cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-ss', '00:00:01', '-vframes', '1',
                thumb_path
            ]
            process_thumb = subprocess.run(thumb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process_thumb.returncode == 0:
                extracted_thumb = True
                print("Miniature extraite avec succès !")
            else:
                print(f"Échec de l'extraction de miniature : {process_thumb.stderr.decode('utf-8', errors='ignore')}")

        # 4. Enregistrer les fichiers traités dans l'instance de modèle
        # Enregistrer la vidéo compressée (seulement si la compression a fonctionné et créé un fichier différent)
        if compressed_path != input_path:
            with open(compressed_path, 'rb') as f:
                video.video_file.save(
                    os.path.basename(video.video_file.name),
                    ContentFile(f.read()),
                    save=False
                )

        # Enregistrer la miniature extraite
        if extracted_thumb:
            with open(thumb_path, 'rb') as f:
                video.thumbnail_file.save(
                    f"{video.slug}_thumb.jpg",
                    ContentFile(f.read()),
                    save=False
                )

        # Sauvegarder définitivement le modèle
        video._ffmpeg_processed = True
        video.save()
        print(f"Traitement de la vidéo {video.title} terminé avec succès !")

    finally:
        # 5. Nettoyage des fichiers temporaires locaux
        if temp_input and os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        if os.path.exists(compressed_path) and compressed_path != input_path:
            os.unlink(compressed_path)
        if os.path.exists(thumb_path):
            os.unlink(thumb_path)

    return f"Traitement vidéo ID {video_id} complété."
