# ==============================================================================
# STAGE 1 : BUILDER (Compilation des dépendances)
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Désactiver la mise en cache de pip et l'écriture des fichiers pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dépendances système requises pour compiler psycopg2 et pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt et construire les wheel files
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# STAGE 2 : RUNTIME (Image finale légère de production)
# ==============================================================================
FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Installer les dépendances d'exécution système (libpq pour PostgreSQL, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libwebp7 \
    zlib1g \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les packages python construits dans l'étape builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copier l'intégralité du code de l'application
COPY . .

# Créer les dossiers de stockage locaux par défaut
RUN mkdir -p /app/staticfiles /app/media

# Créer un utilisateur non-privilégié pour la sécurité du conteneur
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

# Exposer le port de Gunicorn
EXPOSE 8000

# Commande par défaut (lancement de l'application Django via Gunicorn)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
