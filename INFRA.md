# Shared Infrastructure — StudsUp & LatLUG
*Common reference for both Claude Projects. Secrets are redacted — keep actual
credentials in your password manager and paste per-conversation when needed.*
*Last updated: 2026-07-08*

---

## 1. Server

| | |
|---|---|
| Provider | Hetzner Cloud, CX23, Helsinki |
| IP | `65.21.152.253` |
| OS | Ubuntu 24.04 |
| SSH user | `root` |
| Auth | SSH key preferred (see §4); root password in password manager |
| Console fallback | Hetzner noVNC — **avoid**: mangles keyboard input (see §7) |

Currently hosts **studsup.eu**. Adding a second site (e.g. LatLUG) = new nginx
vhost + certbot cert on the same box; plenty of headroom for static sites.

## 2. studsup.eu layout (reference pattern for any new site)

```
Nginx (SSL via certbot, DNS → Hetzner IP)
 ├─ /            static frontend   /app/studsup/frontend  (18 HTML pages)
 ├─ /api/*       FastAPI + uvicorn, port 8000, systemd service "studsup"
 ├─ /uploads/*   user uploads, catalog PDFs + thumbnails
 ├─ /images/*    local part-image cache
 └─ /ldraw/*     LDraw part library (24,216 parts, ~601 MB)

Data: SQLite (WAL mode) at /app/studsup/backend/db/studsup.db
      78k+ parts, 27k sets, users/collections/posts
```

Clients: responsive web, installable **PWA** (`manifest.webmanifest` + passthrough
`sw.js`, updates on every deploy), optional **Flutter app** (`mobile/` in repo,
built manually — native login + live QR scanner + WebView shell).

## 3. Deploy pipeline (pattern to replicate per project)

```
git push → main (GitHub, private repo)
   └─► GitHub Actions (.github/workflows/deploy.yml)
        secrets: DEPLOY_KEY (SSH private key), SERVER_HOST
        └─► ssh root@server → /usr/local/bin/studsup-deploy
             (git pull + systemctl restart studsup)
```

- Every push to `main` auto-deploys; green in ~60–70 s.
- Manual trigger: `POST /repos/<owner>/<repo>/actions/workflows/deploy.yml/dispatches`
  with `{"ref":"main"}` and a PAT, or `workflow_dispatch` in the Actions UI.
- Server helper scripts: `studsup-push "msg"` (commit+push),
  `studsup-deploy` (pull+restart), `studsup-sync "msg"` (both).
- StudsUp gotcha: root `index.html` must stay in sync with `frontend/index.html`.

**GitHub repos:** `github.com/obzorik/studsup` (private),
`github.com/obzorik/latlug-website` (bilingual LV/EN, nginx + Docker).

**⚠ PAT expiry:** the GitHub personal access token expires **2026-07-20**.
Renew before then or pushes/API triggers from tooling stop working.

## 4. Local tooling (your PC)

- **`studsup-ssh` Docker container** — the bridge for SSH work:
  - `/root/.ssh/id_ed25519` → server SSH key
  - `/root/.ssh/id_github` → GitHub deploy key (write); global
    `url.insteadOf` rewrite set for `git@github.com`
  - repo cloned at `/work/studsup`
  - usage: `docker exec -it studsup-ssh ssh root@65.21.152.253`
- **Portainer** at `https://localhost:9443` (password in password manager).
  - Container *console* in Portainer freezes browser tabs — use the API instead:
    `GET /api/endpoints/3/docker/containers/json` returns an `X-CSRF-Token`
    header (XHR only) → include it in POST exec requests. On session expiry,
    re-login (AngularJS ngModel fill + button click).

## 5. Secondary deploy targets (legacy, StudsUp)

- **Render.com** — publish dir `frontend/`, `Cache-Control: no-cache` on `/*`
  set in dashboard. `render.yaml` removed from repo; dashboard-managed only.
  Pending: ANTHROPIC_API_KEY env var, $5 spend cap.
- **GitHub Pages** — auto-deploys static frontend on push (no API).

## 6. Claude-in-Chrome quirks (apply to any project)

- Extension drops connection after long-running JS / frozen tabs; recover via
  `tabs_context_mcp` with `createIfEmpty`, or restart the extension.
- Three.js canvases and large PDFs (20–150 MB in PDF.js) freeze tabs — open in
  a separate tab, switch away to recover.
- Cloudflare dashboard is a blank SPA in the extension — unusable; do
  Cloudflare tasks manually.
- JS-based interaction (`element.click()`, dispatched events) beats coordinate
  clicks; `read_console_messages` filtered on `error|401|fail|auth|token` is
  the fastest diagnosis tool.
- Screenshots after JS need 2–4 s settle delay for async work.

## 7. Hetzner noVNC console (emergency only)

- Mangles keyboard: underscores→hyphens, `@`→`2`, special chars corrupted.
- Workaround: base64-encode scripts →
  `echo <b64> | base64 -d > /tmp/s.sh && bash /tmp/s.sh`
- A stuck heredoc survives page reload — only a server power cycle clears it.
- Most reliable in-console editor: `nano`, save with F2.

## 8. Hard-won engineering rules (both projects)

- **Never seed test data into real accounts.** Test writes must clean up in the
  same session or use a throwaway account. (Root cause of the StudsUp
  "random parts reappearing" mystery.)
- **Watch one-to-many JOIN multiplication** — bit StudsUp four times
  (search, set import, build checker, element images). Dedupe with a
  `LIMIT 1` subquery on the joined side.
- **No inline `onerror`/`onclick` JS with nested quotes** — browsers silently
  drop handlers with syntax errors. Use delegated listeners (capture phase for
  `error` events) or `data-*` attributes.
- `node --check` every touched script and `python -c "import ast; ast.parse(...)"`
  every backend change **before** deploying.
- Verify pages make real API calls — several StudsUp pages were static mocks
  that looked functional (profile, checker, Have/Want buttons).
- `sessionStorage` is per-tab; auth guards should use API 401 detection, not
  immediate redirects.
- `loading="lazy"` on images breaks on Samsung mobile — avoid on key content.

## 9. Credentials index (values in password manager, not here)

| Secret | Where used |
|---|---|
| Hetzner root password | SSH fallback, Hetzner console |
| GitHub PAT (**expires 2026-07-20**) | HTTPS pushes, Actions API triggers |
| GitHub DEPLOY_KEY / SERVER_HOST | Actions secrets (already configured) |
| Portainer admin password | localhost:9443 |
| StudsUp admin login | georgs@studsup.com (demo password) |
| StudsUp test users | brickfan@ / newbrick@ studsup.eu |
