# LatLUG — new website (prototype)

Bilingual (LV/EN) homepage concept for the LatLUG website rebuild.
Static site served by nginx in Docker.

## Files

- `index.html` — the whole prototype (HTML + CSS + JS, LV/EN toggle)
- `Dockerfile` — nginx:alpine serving the page
- `docker-compose.yml` — runs the container on port **8085**

## Deploy with Portainer (from this repo)

1. Portainer → Stacks → **Add stack** → Build method: **Repository**
2. Repository URL: https://github.com/obzorik/latlug-website
   - Repo is **private** → enable Authentication and use a GitHub fine-grained PAT (read-only, this repo only)
3. Compose path: `docker-compose.yml` → Deploy
4. Site is available on http://<host>:8085

Alternative without git auth: Stacks → Add stack → **Web editor**, paste the compose contents, replacing `build:` with a plain nginx:alpine image + bind-mount of `index.html`.

## Deploy on the studsup Hetzner server (nginx route)

Same pattern as studsup.eu: add an nginx server block for new.latlug.lv (or latlug.studsup.eu), point root at a folder with index.html, run certbot for HTTPS, add the DNS A record.

## Editing texts

Every translatable element has `data-lv` and `data-en` attributes — update both when changing copy.
