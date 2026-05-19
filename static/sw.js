const CACHE_NAME = 'dorocaviar-v1';
const ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/manifest.json',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png'
];

// Installation du service worker et mise en cache des assets de base
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activation et nettoyage des anciens caches
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Strategie de Fetch : Network-First pour les pages dynamiques, Cache-First pour les assets
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // Eviter de cacher les requetes admin, POST ou non-GET
  if (e.request.method !== 'GET' || url.pathname.startsWith('/admin/') || url.pathname.startsWith('/accounts/sse/')) {
    return;
  }

  // Strategie Cache-First pour les CSS, JS et images
  if (
    e.request.destination === 'style' ||
    e.request.destination === 'script' ||
    e.request.destination === 'image' ||
    url.pathname.startsWith('/static/')
  ) {
    e.respondWith(
      caches.match(e.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(e.request).then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(e.request, networkResponse.clone());
            return networkResponse;
          });
        });
      })
    );
  } else {
    // Strategie Network-First pour les autres requetes (HTML/pages dynamiques)
    e.respondWith(
      fetch(e.request)
        .then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            cache.put(e.request, networkResponse.clone());
            return networkResponse;
          });
        })
        .catch(() => {
          return caches.match(e.request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Page de fallback si hors-ligne total
            return caches.match('/');
          });
        })
    );
  }
});
