const CACHE_NAME = 'artificiall-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/css/style.css',   // Corrigido para style.css (caminho correto)
  '/js/main.js'
  // Adicionar outros assets importantes depois (fontes originais, logos, imagens)
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
