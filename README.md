# EpitaCampus

Site personnel de révision pour les études à l'EPITA, hébergé sur un Raspberry Pi 4.

- **Tableau de bord** : cours du jour, examens à venir avec sessions de révision conseillées (J-7, J-3, J-1), cours à réviser, moyenne générale.
- **Cours** : une fiche par cours avec notes et fichiers (PDF…), et révision espacée (1, 3, 7, 14, 30, 60 jours).
- **Calendrier** : synchronisation automatique d'un lien ICS (Zeus, Google Agenda…) toutes les 30 min, ajout manuel d'examens.
- **Notes** : saisie des notes, moyenne pondérée, moyenne par matière et évolution.
- **Outils** : PDF (fusion, extraction, rotation), JWT (décodage, vérification HMAC), minuteur Pomodoro.

## Architecture

| Service   | Rôle                                                                 |
|-----------|----------------------------------------------------------------------|
| `caddy`   | Sert le frontend SvelteKit compilé et redirige `/api/*` vers le backend |
| `backend` | API FastAPI (Python), fichiers déposés dans le volume `uploads`      |
| `db`      | PostgreSQL 17, données dans le volume `pgdata`                       |

## Développement sur le Mac

Backend (base SQLite locale `backend/dev.db`, aucun Docker nécessaire) :

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/fastapi dev app/main.py
```

Frontend (dans un autre terminal), puis ouvrir http://localhost:5173 :

```bash
cd frontend
npm install
npm run dev
```

La documentation interactive de l'API est sur http://localhost:8000/api/docs.

Pour tester la version « production » complète : `docker compose up -d --build` puis http://localhost.

## Déploiement sur le Raspberry Pi

Première installation (sur le Pi, en SSH) :

```bash
git clone git@github.com:AEG1X/EpitaCampus.git ~/EpitaCampus
cd ~/EpitaCampus
cp .env.example .env
nano .env   # mot de passe PostgreSQL + SECRET_KEY (openssl rand -hex 32)
docker compose up -d --build
```

Mises à jour suivantes :

```bash
cd ~/EpitaCampus && git pull && docker compose up -d --build
```

Le site est ensuite accessible sur http://campus (via Tailscale) ou http://<ip-du-pi>.
Le tout premier compte créé devient administrateur ; ensuite les inscriptions sont fermées
(mettre `ALLOW_SIGNUP=true` dans `.env` pour en ouvrir d'autres).

Sauvegarde de la base :

```bash
docker compose exec db pg_dump -U campus campus > sauvegarde-$(date +%F).sql
```
