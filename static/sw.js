// Minimal Service Worker for Reality Checker dashboard
// Scope: /

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  self.clients.claim();
});

// No-op fetch handler (can be extended to add caching if needed)
self.addEventListener('fetch', () => {});

