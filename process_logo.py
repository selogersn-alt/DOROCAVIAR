import os
import django
from PIL import Image

# Initialize Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.marketing.models import PlatformSettings

source_path = r"C:\Users\mursd\.gemini\antigravity\brain\5f668ea1-7848-4853-8410-17a187945d05\uploaded_media_1776710545058.png"

def process():
    if not os.path.exists(source_path):
        print(f"File not found: {source_path}")
        return

    # Process Logo
    img = Image.open(source_path)
    
    # We want to keep transparency if present
    img = img.convert("RGBA")
    
    media_settings_dir = os.path.join('media', 'settings')
    os.makedirs(media_settings_dir, exist_ok=True)
    
    logo_path = os.path.join(media_settings_dir, 'dorocaviar_logo.png')
    img.save(logo_path, format="PNG")

    # Process Favicon
    favicon_path = os.path.join(media_settings_dir, 'favicon.ico')
    icon = img.resize((32, 32), Image.Resampling.LANCZOS)
    icon.save(favicon_path, format='ICO')

    # Update DB
    settings, _ = PlatformSettings.objects.get_or_create(pk=1)
    settings.logo.name = 'settings/dorocaviar_logo.png'
    settings.favicon.name = 'settings/favicon.ico'
    settings.save()
    print("Logo and Favicon successfully processed and updated in the database.")

if __name__ == "__main__":
    process()
