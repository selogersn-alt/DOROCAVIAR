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
