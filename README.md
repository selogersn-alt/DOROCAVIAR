# Dorocaviar - Video Aggregator Platform

Dorocaviar is a high-performance, automated video aggregator built with Django. It allows for seamless content synchronization via APIs and scraping, optimized for SEO and monetization.

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- PostgreSQL
- Redis (for Celery and Caching)

### 2. Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Setup Database
python manage.py makemigrations
python manage.py migrate

# Create Admin
python manage.py createsuperuser
```

### 3. Background Workers
To start the import engine:
```bash
celery -A core worker -l info
```

## 📂 Architecture
- **apps.videos**: Core video management and import logic.
- **apps.users**: User profiles and social features (favorites/history).
- **apps.marketing**: SEO (sitemaps, robots) and Monetization (ads, affiliate links).

## 🛠️ Key Features
- **Automated Import**: Extendable `BaseImporter` for JSON APIs and BeautifulSoup Scraping.
- **Advanced SEO**: Automatic slugs, sitemaps, and dynamic meta tags.
- **Premium Design**: Modern dark UI with glassmorphism effects.
- **Monetization**: Integrated ad placement system and affiliate tracking.

## 🎯 Admin Access
Access the advanced dashboard at `/admin/` to manage imports, validate content, and track performance.
