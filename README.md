# Purify - 정화의 길 (PWA)

정적 파일만으로 동작합니다. 서버/DB 없음 — 기록은 각 사용자 기기의 localStorage에 저장됩니다.

## 배포 (택1)
- GitHub Pages: 이 폴더 내용을 공개 저장소 루트에 올리고 Settings → Pages → Branch: main / (root)
- Netlify: app.netlify.com/drop 에 이 폴더(또는 purify-site.zip)를 끌어다 놓기
- Cloudflare Pages: Workers & Pages → Create → Pages → Upload assets

HTTPS에서 열어야 설치(홈 화면에 추가)와 오프라인이 동작합니다.
앱을 수정하면 sw.js의 CACHE 이름(purify-v3-1)을 올려 주세요.
