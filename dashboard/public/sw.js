// Minimal Service Worker scoped to the dashboard

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  self.clients.claim();
});

// Placeholder fetch handler; extend to add caching for dashboard assets
self.addEventListener('fetch', () => {});

