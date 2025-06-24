# Plan Détaillé de Correction pour la Synchronisation des Commandes du Bot

_Version 1.1 - Enrichie des résultats de la session de débogage._

## 1. Contexte et Problème

L'objectif est d'assurer une communication fiable entre le tableau de bord web et le bot de trading. L'enquête a révélé que si l'état du bot remonte bien vers le tableau de bord, les commandes descendantes (ex: passer en mode `ACTIVE`) n'sont pas exécutées par le bot.

### 1.1. Analyse de l'Architecture

- **Frontend** : Application React (Vite) tournant sur `localhost:5173`.
- **Backend** : Serveur FastAPI (Uvicorn) sur `localhost:8000`.
- **Bot** : Script Python `main.py` qui lance `AlloraMind`.
- **Communication** :
  1.  **Frontend -> Backend (API/WebSocket)** : L'utilisateur interagit avec le frontend, qui envoie des requêtes HTTP (pour les actions) et maintient une connexion WebSocket (pour les données temps réel) avec le backend. **Cette partie est fonctionnelle.**
  2.  **Backend -> Base de Données (Écriture)** : En réponse à une commande de l'API, le `BotModeController` du backend insère une nouvelle ligne dans la table `bot_commands` de la base de données SQLite. **Cette partie est fonctionnelle,** comme le montrent les logs du backend (`📨 Added bot command...`).
  3.  **Bot -> Base de Données (Lecture)** : Le processus du bot, dans sa boucle `check_dashboard_commands`, est censé interroger la table `bot_commands`, lire les commandes en attente et les exécuter. **C'est le maillon faible qui est défaillant.**

### 1.2. Diagnostics et Cause Racine

- **Problème de Démarrage Initial** : Nous avons découvert que le `BotProcessController` du backend ne pouvait pas lancer le bot `main.py` directement à cause d'une `UnicodeEncodeError` (liée à l'emoji 🚀 dans un `print`) lorsque `stdout` est redirigé. Le contournement actuel consiste à lancer le bot manuellement.
- **Cause Racine de l'Échec des Commandes** : Le bot, bien qu'en cours d'exécution, ignore les commandes présentes dans la base de données. Le diagnostic pointe vers un **problème de concurrence et de synchronisation avec la base de données SQLite**. SQLite, étant une base de données embarquée dans un fichier, gère difficilement l'accès concurrent en lecture/écriture par des processus complètement distincts (le backend et le bot). Il est très probable que la connexion du bot à la base de données ne voie pas les `COMMIT` effectués par le processus du backend, soit à cause du caching de la connexion, soit à cause du mode de verrouillage par défaut du fichier de la base de données.

## 2. Plan d'Action Détaillé

### Option A : Fiabiliser l'Implémentation SQLite (Effort Moyen)

L'objectif est de configurer SQLite pour une meilleure gestion de la concurrence.

- **Étape 1 : Activer le mode "Write-Ahead Logging" (WAL)**

  - **Quoi :** Le mode WAL est un mécanisme de journalisation qui permet à des opérations de lecture de se produire simultanément à une opération d'écriture. C'est le mode recommandé pour les applications concurrentes.
  - **Comment :** Dans `database/db_manager.py`, après chaque création de connexion, exécuter la commande `PRAGMA`.

    ```python
    # Dans db_manager.py
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10) # Ajouter un timeout
        conn.execute("PRAGMA journal_mode=WAL;") # Activer le mode WAL
        return conn

    # Remplacer tous les appels à sqlite3.connect() par self._get_connection()
    ```

- **Étape 2 : Revoir la Gestion des Transactions**
  - **Quoi :** S'assurer que chaque opération est atomique et que les connexions ne sont pas réutilisées de manière incorrecte entre les fonctions.
  - **Comment :** Envelopper chaque lecture et écriture dans sa propre fonction qui gère le cycle complet `connexion -> curseur -> exécution -> commit/close`. La structure actuelle du `db_manager.py` est déjà assez proche de ce modèle, mais une vérification est nécessaire pour garantir qu'aucune connexion n'est laissée ouverte.

### Option B : Mettre en Place une File d'Attente par Fichiers (Recommandé, Effort Moyen)

Cette approche élimine complètement le problème de concurrence sur la base de données pour les commandes.

- **Étape 1 : Créer la Structure de Répertoires**

  - Créer un répertoire `tmp/commands/` à la racine du projet, qui contiendra deux sous-répertoires : `pending` et `processed`.

- **Étape 2 : Modifier le Backend pour Écrire des Fichiers de Commande**

  - **Où :** `dashboard/backend/controllers/bot_mode_controller.py` et `database/db_manager.py` (dans `add_bot_command`).
  - **Logique :** Au lieu d'un `INSERT` en base de données, la fonction créera un fichier.

    ```python
    # Dans db_manager.py (ou une nouvelle classe CommandManager)
    import uuid

    def add_bot_command(self, command_type, command_data=None):
        command_dir = os.path.join(self.project_root, "tmp", "commands", "pending")
        os.makedirs(command_dir, exist_ok=True)

        command_id = str(uuid.uuid4())
        file_path = os.path.join(command_dir, f"{command_id}.json")

        command_content = {
            "id": command_id,
            "command_type": command_type,
            "data": command_data,
            "timestamp": datetime.now().isoformat()
        }

        with open(file_path, "w") as f:
            json.dump(command_content, f)

        print(f"📨 Fichier de commande créé : {file_path}")
    ```

- **Étape 3 : Modifier le Bot pour Lire les Fichiers de Commande**

  - **Où :** `allora/allora_mind.py` (dans `check_dashboard_commands`).
  - **Logique :** La fonction lira le répertoire `pending`, traitera chaque fichier, puis le déplacera.

    ```python
    # Dans allora_mind.py
    def check_dashboard_commands(self):
        command_dir = os.path.join(self.project_root, "tmp", "commands", "pending")
        processed_dir = os.path.join(self.project_root, "tmp", "commands", "processed")

        if not os.path.exists(command_dir): return

        for filename in os.listdir(command_dir):
            filepath = os.path.join(command_dir, filename)
            try:
                with open(filepath, "r") as f:
                    command = json.load(f)

                print(f"🤖 Commande trouvée : {command['command_type']}")
                success = self.execute_command(command)

                # Déplacer vers 'processed' pour l'audit
                os.rename(filepath, os.path.join(processed_dir, filename))
            except Exception as e:
                print(f"❌ Erreur de traitement du fichier de commande {filename}: {e}")
                # Déplacer vers un répertoire 'failed' pourrait être une bonne idée
    ```

### Option C : Migration vers PostgreSQL (Solution à Long Terme, Effort Élevé)

- **Description :** Remplacer SQLite par une base de données client-serveur qui est conçue nativement pour la concurrence.
- **Impact :**
  - Nécessite une instance PostgreSQL en cours d'exécution.
  - Ajouter `psycopg2-binary` à `requirements.txt`.
  - Mettre à jour la logique de connexion dans `db_manager.py` pour utiliser la chaîne de connexion de PostgreSQL (depuis le fichier `.env`).
  - Cette solution est la plus robuste mais représente un changement d'infrastructure significatif.

## 3. Recommandation Stratégique

1.  **Correction Immédiate :** Mettre en œuvre la **Solution B (File d'attente par Fichiers)**. C'est la solution qui garantit le plus haut niveau de fiabilité pour résoudre le problème spécifique de la communication des commandes avec un effort de développement raisonnable. Elle découple proprement les processus.
2.  **Amélioration future :** Garder la **Solution C (Migration vers PostgreSQL)** en tête pour une future version du projet si les besoins en matière de base de données (analyses complexes, plus d'écritures concurrentes) venaient à augmenter.
