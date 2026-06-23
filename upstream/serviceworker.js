/* 2026-05-08 — kill-switch service worker.
 *
 * Background:
 *   meetgreeksingles.com is a PWA-flagged site (manifest.php is served).
 *   At some point Chameleon registered a service worker that cached
 *   responses; after we put the prelaunch gate in front of routes, the
 *   /serviceworker.js URL started 302'ing back to the homepage, which
 *   meant browsers couldn't update the SW and were left running stale
 *   cached logic. Symptom: Irene's normal Chrome session intercepts
 *   button clicks with stale state ("nothing happens"), while Incognito
 *   (no SW) works fine.
 *
 * What this does:
 *   1) On install: take over immediately (skipWaiting) so no leftover
 *      worker keeps running.
 *   2) On activate: delete every cache, unregister this worker, and
 *      navigate any open page of the site to itself so the user gets a
 *      clean fetch from the network.
 *
 * What this does NOT do:
 *   - It does not register itself. A user's browser only ever loads this
 *     file if it already had an SW registered for this origin. Fresh
 *     visitors with no SW history hit the homepage, the homepage doesn't
 *     call navigator.serviceWorker.register(), so nothing changes for them.
 *   - It does not cache anything for offline use. If we want a real PWA
 *     SW post-launch, that's a separate file we can build deliberately.
 */

self.addEventListener('install', function (event) {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil((async function () {
        try {
            var keys = await caches.keys();
            await Promise.all(keys.map(function (k) { return caches.delete(k); }));
        } catch (e) { /* ignore */ }
        try {
            await self.registration.unregister();
        } catch (e) { /* ignore */ }
        try {
            var clients = await self.clients.matchAll({ type: 'window' });
            clients.forEach(function (client) {
                if (client && client.url) client.navigate(client.url);
            });
        } catch (e) { /* ignore */ }
    })());
});

/* Defensive: don't intercept fetches. If the browser asks for a resource,
 * pass it straight through to the network. (Without this listener,
 * browsers would still default to network — but being explicit avoids any
 * inherited Cache-First behaviour from the previous SW that the install
 * event might race against on first activation.) */
self.addEventListener('fetch', function (event) {
    /* no-op — let the browser handle it */
});
