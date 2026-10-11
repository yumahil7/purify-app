// Purify service worker — 오프라인 캐시 (사용자 데이터는 localStorage에 있으며 SW는 건드리지 않음)
const CACHE = 'purify-v3-4';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './favicon.png',
  './icons/icon-192.png', './icons/icon-512.png', './icons/icon-512-maskable.png', './icons/apple-touch-icon.png',
  './audio/purify-bgm.mp3'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('purify-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// <audio>가 보내는 Range 요청에 캐시된 파일로 206 응답 (iOS Safari 호환)
async function rangeResponse(req, res) {
  const buf = await res.arrayBuffer(), total = buf.byteLength;
  const m = /bytes=(\d*)-(\d*)/.exec(req.headers.get('range') || '');
  let start = 0, end = total - 1;
  if (m) {
    if (m[1] === '' && m[2] !== '') { start = Math.max(0, total - +m[2]); }
    else { start = +m[1] || 0; if (m[2] !== '') end = Math.min(+m[2], total - 1); }
  }
  if (start >= total) return new Response(null, { status: 416, headers: { 'Content-Range': 'bytes */' + total } });
  return new Response(buf.slice(start, end + 1), { status: 206, headers: {
    'Content-Type': res.headers.get('Content-Type') || 'application/octet-stream',
    'Content-Range': 'bytes ' + start + '-' + end + '/' + total, 'Content-Length': String(end - start + 1), 'Accept-Ranges': 'bytes' } });
}
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  if (req.mode === 'navigate') {
    // 페이지: 네트워크 우선(업데이트 반영), 오프라인이면 캐시
    e.respondWith(fetch(req).then(res => { if (res.status === 200) { const copy = res.clone(); caches.open(CACHE).then(c => c.put('./index.html', copy)); } return res; })
      .catch(() => caches.match('./index.html').then(r => r || caches.match('./'))));
    return;
  }
  if (req.headers.has('range')) {
    e.respondWith(caches.match(req.url).then(hit => hit ? rangeResponse(req, hit) : fetch(req)));
    return;
  }
  // 정적 파일: 캐시 우선, 없으면 네트워크 후 저장 (200만 저장)
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.status === 200) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  })));
});
