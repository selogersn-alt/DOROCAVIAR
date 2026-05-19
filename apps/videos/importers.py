import requests
from bs4 import BeautifulSoup
from .models import Video, Category, ImportSource

class BaseImporter:
    def __init__(self, source):
        self.source = source
        self.config = source.config

    def clean_text(self, text):
        return text.strip() if text else ""

    def save_video(self, video_data):
        """Logique anti-doublons: on se base sur l'URL de l'embed ou la source."""
        embed_url = video_data.get('embed_url')
        if not embed_url:
            return False, "Pas d'URL d'embed"

        # Anti-doublons: chercher si la vidéo existe déjà
        video, created = Video.objects.get_or_create(
            embed_url=embed_url,
            defaults={
                'title': self.clean_text(video_data.get('title', 'Sans Titre')),
                'description': self.clean_text(video_data.get('description', '')),
                'thumbnail': video_data.get('thumbnail', ''),
                'source_url': video_data.get('source_url', ''),
            }
        )
        
        # Gestion des tags s'ils sont fournis
        tags = video_data.get('tags', [])
        if tags and created:
            video.tags.add(*tags)
            
        return created, video

class APIImporter(BaseImporter):
    def run(self):
        print(f"Starting API import from {self.source.name}")
        response = requests.get(self.source.base_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Logic depends on JSON structure defined in config
            # Example: data['videos']
            results = self.process_data(data)
            return results
        return None

    def process_data(self, data):
        # Implementation of JSON mapping
        # Ce code va dépendre de `self.config` (Stocké en JSON dans l'Admin)
        # Mais voici un exemple générique:
        
        videos_added = 0
        items = data.get('items', []) # Exemple générique
        for item in items:
            video_data = {
                'title': item.get('title'),
                'description': item.get('description'),
                'embed_url': item.get('iframe_url'),
                'thumbnail': item.get('image_url'),
                'tags': item.get('keywords', [])
            }
            
            created, obj = self.save_video(video_data)
            if created:
                videos_added += 1
                
        return {"added": videos_added, "processed": len(items)}

class ScrapingImporter(BaseImporter):
    def run(self):
        print(f"Starting Scraping from {self.source.name}")
        response = requests.get(self.source.base_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Logic depends on CSS selectors in config
            results = self.extract_videos(soup)
            return results
        return None

    def extract_videos(self, soup):
        """Extraction de vidéos basée sur des sélecteurs CSS définis dans ImportSource.config."""
        config = self.source.config or {}
        item_selector = config.get('item_selector')
        title_selector = config.get('title_selector')
        link_selector = config.get('link_selector')
        thumb_selector = config.get('thumbnail_selector')
        
        if not item_selector:
            return {"error": "Sélecteur d'item manquant dans la configuration"}

        videos_added = 0
        items = soup.select(item_selector)
        
        for item in items:
            try:
                title_tag = item.select_one(title_selector) if title_selector else None
                link_tag = item.select_one(link_selector) if link_selector else item
                thumb_tag = item.select_one(thumb_selector) if thumb_selector else None
                
                source_url = link_tag.get('href') if link_tag else None
                if source_url and not source_url.startswith('http'):
                    # Gérer les URLs relatives
                    from urllib.parse import urljoin
                    source_url = urljoin(self.source.base_url, source_url)

                video_data = {
                    'title': title_tag.get_text(strip=True) if title_tag else "Sans titre",
                    'source_url': source_url,
                    'thumbnail': thumb_tag.get('src') if thumb_tag else None,
                }
                
                # Note: L'embed_url est souvent difficile à scraper en une passe.
                # Ici on peut soit générer un embed type YouTube/Pornhub si on reconnaît l'URL,
                # soit prévoir une deuxième passe de visite de la page source_url.
                
                # Logique simplifiée de transformation d'URL en Embed
                if source_url:
                    video_data['embed_url'] = self.convert_to_embed(source_url)

                if video_data.get('embed_url'):
                    created, obj = self.save_video(video_data)
                    if created:
                        videos_added += 1
            except Exception as e:
                print(f"Error extracting item: {e}")
                continue
                
        return {"added": videos_added, "processed": len(items)}

    def convert_to_embed(self, url):
        """Tente de transformer une URL classique en URL d'intégration."""
        if 'youtube.com/watch?v=' in url:
            return url.replace('watch?v=', 'embed/')
        if 'vimeo.com/' in url:
            return url.replace('vimeo.com/', 'player.vimeo.com/video/')
        # On peut ajouter d'autres patterns ici
        return None

def trigger_import_task(source_id):
    source = ImportSource.objects.get(id=source_id)
    if source.source_type == 'API':
        importer = APIImporter(source)
    else:
        importer = ScrapingImporter(source)
    
    return importer.run()
