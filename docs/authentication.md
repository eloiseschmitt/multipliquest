# Authentification

MultipliQuest utilise l'authentification Django avec des sessions serveur et un cookie de session `HttpOnly`.
Le cookie est marqué `Secure` quand `DJANGO_DEBUG=false`. Les requêtes qui modifient des données gardent la protection CSRF.

## Création du premier parent

Il n'y a pas d'inscription publique parent. Créer le premier compte via Django Admin :

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Dans `/admin/`, définir le rôle du compte à `PARENT`. Ce parent peut ensuite créer un compte enfant via `POST /api/children/`.

## Variables d'environnement

Copier `.env.example` hors dépôt et définir de vraies valeurs en production. Ne pas committer de secret réel.

Les origines React autorisées doivent être listées dans `DJANGO_CORS_ALLOWED_ORIGINS` et `DJANGO_CSRF_TRUSTED_ORIGINS`.
