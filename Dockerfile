# ==============================================================================
# STAGE 1 : BUILDER (Compilation des dependances)
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Desactiver la mise en cache de pip et l'ecriture des fichiers pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dependances systeme requises pour compiler psycopg2 et pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Creer un environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier requirements.txt et construire les wheel files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# STAGE 2 : RUNTIME (Image finale legere de production)
# ==============================================================================
FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PATH="/opt/venv/bin:$PATH"

# Installer les dependances d'execution systeme (libpq pour PostgreSQL, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libwebp7 \
    zlib1g \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les packages python construits dans l'etape builder
COPY --from=builder /opt/venv /opt/venv

# Copier l'integralite du code de l'application
COPY . .

# Creer les dossiers de stockage locaux par defaut
RUN mkdir -p /app/staticfiles /app/media

# Creer un utilisateur non-privilegie pour la securite du conteneur
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app /opt/venv
USER appuser

# Exposer le port de Gunicorn
EXPOSE 8000

# Commande par defaut (lancement de l'application Django via Gunicorn)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
