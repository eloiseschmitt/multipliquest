# Deploiement de test sur Render

Ce guide prepare un premier deploiement de test de MultipliQuest sur Render avec trois ressources:

- `multipliquest-frontend`: Static Site Render pour le build React/Vite.
- `multipliquest-api`: Web Service Render pour Django, Django Admin et l'API.
- `multipliquest-db`: Render Postgres, relie au backend par `DATABASE_URL`.

Ne deploie pas de donnees reelles d'enfant sur le plan gratuit. Les comptes parent/enfant de test se creent exclusivement dans Django Admin.

## Architecture et choix

- Le frontend est un site statique. Il appelle l'API publique Django via `VITE_API_BASE_URL`.
- Le backend utilise les sessions Django, les cookies `Secure`, CSRF Django et CORS limite a l'origine du frontend.
- L'endpoint `/api/auth/csrf/` pose le cookie CSRF Django et renvoie aussi le token en JSON, necessaire parce que le frontend et le backend sont sur deux origines Render distinctes.
- Le backend lit `DATABASE_URL` en production. Sans `DATABASE_URL`, le developpement local continue d'utiliser `db.sqlite3`.
- `collectstatic` utilise WhiteNoise pour les assets Django Admin.
- Les migrations sont executees par `preDeployCommand` avant le demarrage du service web.

## Variables d'environnement

Le fichier `render.yaml` configure les variables suivantes sans secret versionne:

| Service | Variable | Valeur |
| --- | --- | --- |
| API | `PYTHON_VERSION` | `3.14.3` |
| API | `DJANGO_SECRET_KEY` | generee par Render |
| API | `DJANGO_DEBUG` | `false` |
| API | `DJANGO_ALLOWED_HOSTS` | hostname public du service API |
| API | `DJANGO_CSRF_TRUSTED_ORIGINS` | URL publique du frontend |
| API | `DJANGO_CORS_ALLOWED_ORIGINS` | URL publique du frontend |
| API | `DJANGO_SECURE_SSL_REDIRECT` | `true` |
| API | `DJANGO_SECURE_HSTS_SECONDS` | `31536000` |
| API | `SESSION_COOKIE_SAMESITE` | `None` |
| API | `CSRF_COOKIE_SAMESITE` | `None` |
| API | `DATABASE_URL` | connection string interne Postgres |
| Frontend | `VITE_API_BASE_URL` | URL publique du service API |

Variables e-mail optionnelles si l'Admin doit envoyer des messages, par exemple pour une procedure de mot de passe: `DJANGO_EMAIL_BACKEND`, `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`, `DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD`, `DJANGO_EMAIL_USE_TLS`, `DJANGO_DEFAULT_FROM_EMAIL`. Aucun fournisseur SMTP n'est configure dans `render.yaml`; en ajouter un seulement apres validation du mainteneur.

Si des domaines personnalises sont ajoutes plus tard, mettre a jour `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_CORS_ALLOWED_ORIGINS` et reconstruire le frontend avec le nouveau `VITE_API_BASE_URL`.

## Creation sur Render

1. Pousser la branche contenant `render.yaml` vers GitHub.
2. Dans Render, choisir **New > Blueprint** et connecter le depot.
3. Selectionner le fichier `render.yaml`.
4. Verifier les ressources proposees:
   - Web Service `multipliquest-api`, plan `free`.
   - Static Site `multipliquest-frontend`.
   - Postgres `multipliquest-db`, plan `free`.
5. Confirmer que `DJANGO_SECRET_KEY` est generee et qu'aucune valeur secrete n'est saisie dans le depot.
6. Lancer la creation uniquement apres validation explicite du mainteneur.

Les deux services ont `autoDeployTrigger: off`: apres la creation initiale, declencher les deploiements manuellement tant que la CI n'est pas en place.

## Migrations et premier superutilisateur

Les migrations sont lancees automatiquement a chaque deploiement API par:

```bash
uv run python manage.py migrate --noinput
```

Pour creer le premier superutilisateur, utiliser le Shell Render du service API ou un one-off job equivalent, sans mettre de mot de passe dans un script versionne:

```bash
uv run python manage.py createsuperuser
```

Ensuite, dans Django Admin:

1. Creer un compte parent avec `role = PARENT`, `is_staff = false`, `is_superuser = false`.
2. Creer un compte enfant avec `role = CHILD`, `parent = <parent>`, un pseudonyme dans `display_name`, et un mot de passe de test.
3. Ne pas utiliser d'adresse e-mail personnelle d'enfant.

## Verification apres deploiement

1. Ouvrir `https://<api>.onrender.com/api/health/` et verifier `{"status":"ok"}`.
2. Ouvrir `https://<api>.onrender.com/admin/` et verifier que la page Django Admin charge en HTTPS avec les fichiers statiques.
3. Se connecter dans l'Admin avec le superutilisateur cree manuellement.
4. Creer un parent et un enfant de test dans l'Admin.
5. Ouvrir le frontend Render.
6. Se connecter avec le compte enfant de test.
7. Dans les outils navigateur, verifier:
   - `GET /api/auth/csrf/` renvoie 200 et un `csrfToken`.
   - `POST /api/auth/login/` inclut `X-CSRFToken`.
   - Les requetes API utilisent `credentials: include`.
   - Les cookies `sessionid` et `csrftoken` sont `Secure`.
8. Demarrer une session de jeu et verifier qu'aucune reponse correcte n'est exposee avant soumission.

## Sauvegardes et restauration

Le plan Free Render Postgres est uniquement adapte au test:

- La base Free expire 30 jours apres creation.
- Le stockage est limite a 1 GB.
- Render ne fournit pas de sauvegardes, de PITR, ni de logical backups managies sur le plan Free.
- Le service web Free peut s'endormir apres inactivite et redemarrer lentement.
- Le systeme de fichiers du service web est ephemere; ne pas utiliser SQLite en production Render.

Pour un test avec donnees a conserver, passer Postgres sur un plan payant avant de collecter des donnees utiles. Les plans payants donnent acces a la restauration point-in-time et aux exports logiques.

### Export manuel sur plan Free

Depuis une machine locale disposant des outils PostgreSQL, utiliser l'External Database URL de Render:

```bash
pg_dump --format=custom --no-owner --no-acl --file multipliquest.dump "$DATABASE_URL"
```

Stocker le dump hors du depot, dans un emplacement chiffre et controle.

### Restauration depuis un dump

Restaurer uniquement vers une base cible vide ou explicitement destinee a etre remplacee:

```bash
pg_restore --clean --if-exists --no-owner --no-acl --dbname "$DATABASE_URL" multipliquest.dump
uv run python manage.py migrate --noinput
```

Apres restauration, verifier `/api/health/`, l'Admin, la connexion d'un compte de test et le chargement de la progression.

## Commandes locales de verification

Avant de demander un deploiement:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
npm run lint
npm run test
npm run build
DJANGO_DEBUG=false DJANGO_SECRET_KEY=replace-with-a-long-random-secret DJANGO_ALLOWED_HOSTS=localhost DJANGO_CSRF_TRUSTED_ORIGINS=https://app.example.com DJANGO_CORS_ALLOWED_ORIGINS=https://app.example.com uv run python manage.py check --deploy
```

## References Render

- Blueprint YAML: https://render.com/docs/blueprint-spec
- Python version: https://render.com/docs/python-version
- uv version: https://render.com/docs/uv-version
- Static redirects and rewrites: https://render.com/docs/redirects-rewrites
- Free plan limitations: https://render.com/docs/free
- Postgres recovery and backups: https://render.com/docs/postgresql-backups
