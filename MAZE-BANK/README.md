# MAZE BANK — Application de gestion bancaire en micro-services


---

## Architecture

```
   Navigateur ──► frontend (SPA React/Vite, nginx)            http://localhost:8080
        │
        ├──► auth-service        :8001 ──► auth.db   (SQLite)
        ├──► account-service     :8002 ──► accounts.db
        ├──► operation-service   :8003 ──► operations.db
        ├──► validation-service  :8004 ──► validations.db
        └──► log-service         :8005 ──► logs.db
                                   ▲
        tous les services publient leurs logs sur NATS (sujet logs.<service>)
        et le log-service s'y abonne (logs.>) pour les stocker.        NATS :4222
```

- **auth-service** — inscription, connexion (JWT), `/me`, liste des clients.
- **account-service** — comptes, soldes, date de dernière opération, renommage, suppression,
  mouvements internes (crédit / débit / virement).
- **operation-service** — dépôts (immédiats), retraits et virements (en attente de validation).
- **validation-service** — l'agent approuve / rejette ; applique alors les mouvements d'argent.
- **log-service** — s'abonne à NATS (`logs.>`), stocke les logs, expose filtres + statistiques.

Chaque service est une application **FastAPI** indépendante (doc Swagger sur `/docs`)
avec sa **base SQLite** dédiée et ses modèles **SQLModel**. Les appels entre services se
font en HTTP avec la librairie **requests**.

---

## Lancer le projet

Pré-requis : **Docker** + **Docker Compose**.

```bash
docker compose up --build
```

Puis ouvrir **http://localhost:8080**.

Comme on utilise SQLite, il n'y a aucune base à installer ni à attendre : chaque service
crée son fichier de base au démarrage.

Arrêt :

```bash
docker compose down           # garde les données
docker compose down -v        # remet les bases à zéro
```

### Ports

| Service             | URL                       | Doc interactive             |
|---------------------|---------------------------|-----------------------------|
| Frontend (l'app)    | http://localhost:8080     | —                           |
| auth-service        | http://localhost:8001     | http://localhost:8001/docs  |
| account-service     | http://localhost:8002     | http://localhost:8002/docs  |
| operation-service   | http://localhost:8003     | http://localhost:8003/docs  |
| validation-service  | http://localhost:8004     | http://localhost:8004/docs  |
| log-service         | http://localhost:8005     | http://localhost:8005/docs  |
| NATS                | nats://localhost:4222     | —                           |

---

## Étapes pour utiliser la banque

1. **Inscription** — http://localhost:8080 → onglet « Créer un compte » → nom, e-mail,
   type (Client / Agent), mot de passe. Créez au moins **un client** et **un agent**.
2. **Connexion** — onglet « Se connecter ». Un client arrive sur « Mes comptes »,
   un agent sur l'« Espace agent ».
3. **Ouvrir un compte** (client) — bouton « + Ouvrir un compte » (IBAN généré, solde 0 €).
4. **Renommer / supprimer un compte** — boutons sur chaque compte (côté client pour ses
   comptes, côté agent pour n'importe quel compte). La suppression exige un solde à zéro.
5. **Opérations** (client) — dépôt (crédité immédiatement), retrait / virement (en attente).
6. **Validation** (agent) — « Opérations à valider » → Valider (l'argent bouge) ou Rejeter.
7. **Journaux** (agent) — onglet « Journaux » : filtres par service / niveau / période + stats.

---

## Référence des routes (par service)

| Service     | Méthode | Route                        | Rôle requis |
|-------------|---------|------------------------------|-------------|
| auth        | POST    | `/register`                  | —           |
| auth        | POST    | `/login`                     | —           |
| auth        | GET     | `/me`                        | connecté    |
| auth        | GET     | `/clients`                   | agent       |
| account     | GET     | `/accounts`                  | connecté    |
| account     | POST    | `/accounts`                  | connecté    |
| account     | PATCH   | `/accounts/{id}`             | connecté¹   |
| account     | DELETE  | `/accounts/{id}`             | connecté¹   |
| account     | GET     | `/clients/{id}/accounts`     | agent       |
| operation   | POST    | `/operations`                | connecté    |
| operation   | GET     | `/operations/mine`           | connecté    |
| operation   | GET     | `/operations/pending`        | agent       |
| validation  | GET     | `/pending`                   | agent       |
| validation  | POST    | `/{id}/approve`              | agent       |
| validation  | POST    | `/{id}/reject`               | agent       |
| log         | GET     | `/logs`                      | agent       |
| log         | GET     | `/stats`                     | agent       |

> ¹ Renommer / supprimer : un client n'agit que sur ses propres comptes, un agent sur
> n'importe quel compte. La suppression exige un **solde à zéro**.

---

## Développement du frontend (hot-reload)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Le reste de la stack (services + NATS) doit tourner via `docker compose up`.
Le frontend appelle directement les services sur leurs ports (8001..8005).

---

## Pile technique

FastAPI · **SQLModel** · SQLite · NATS (nats-py) · python-jose (JWT) · bcrypt ·
requests (appels inter-services) · React 18 · React Router · Vite · nginx · Docker Compose.
