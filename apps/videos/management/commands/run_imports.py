from django.core.management.base import BaseCommand
from apps.videos.models import ImportSource
from apps.videos.importers import trigger_import_task

class Command(BaseCommand):
    help = 'Lance toutes les sources d\'importation actives (Scraping & API)'

    def handle(self, *args, **options):
        sources = ImportSource.objects.filter(is_active=True)
        self.stdout.write(self.style.SUCCESS(f"Démarrage de l'importation pour {sources.count()} sources..."))
        
        for source in sources:
            self.stdout.write(f"Traitement de : {source.name}...")
            try:
                results = trigger_import_task(source.id)
                if results:
                    self.stdout.write(self.style.SUCCESS(f"Terminé : {results.get('added', 0)} ajoutés, {results.get('processed', 0)} traités."))
                else:
                    self.stdout.write(self.style.WARNING(f"Aucun résultat pour {source.name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur sur {source.name} : {e}"))
                
        self.stdout.write(self.style.SUCCESS("Processus d'importation terminé."))
