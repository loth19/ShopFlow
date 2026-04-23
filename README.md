# ShopFlow Analytics - De la donnée brute au pilotage décisionnel

## 1) Résumé du projet
ShopFlow Analytics est un projet Data orienté métier qui transforme des données e-commerce brutes en indicateurs décisionnels exploitables via:
- un pipeline ETL structuré,
- une API REST FastAPI,
- un dashboard interactif Streamlit.

Objectif principal: montrer une chaîne complète, de la donnée source jusqu'à la restitution business, avec une logique claire, testable et présentable en contexte professionnel.

Ce projet répond à une question simple mais stratégique:
Comment passer d'un ensemble de fichiers CSV hétérogènes à un outil d'analyse fiable pour piloter le chiffre d'affaires, les catégories produits et la performance client?


## 2) Pourquoi ce projet est pertinent
Dans un contexte réel, les équipes métier ont besoin de:
- KPI compréhensibles,
- données cohérentes,
- visualisations actionnables,
- accès API pour intégration applicative.

Ce projet démontre précisément cette capacité, avec une approche progressive:
1. Génération et nettoyage des données.
2. Structuration analytique (ETL).
3. Exposition par API.
4. Visualisation décisionnelle.


## 3) Objectifs métier couverts
- Suivre le revenue global et son évolution.
- Identifier les catégories qui génèrent le plus de valeur.
- Analyser les clients à plus forte contribution.
- Proposer une base extensible pour d'autres analyses (marge, cohortes, churn, segmentation).


## 4) Architecture globale
Le projet repose sur 4 couches complémentaires.

### 4.1 Couche Data (fichiers sources)
- Dossiers `data/raw` et `data/clean`.
- Fichiers clients, commandes et produits.
- Nettoyage pour garantir la qualité des analyses.

### 4.2 Couche ETL / préparation analytique
- Notebooks de transformation et enrichissement.
- Harmonisation des colonnes et des types.
- Gestion des cas réels: valeurs manquantes, cohérence des jointures, filtrage des statuts de commande.

### 4.3 Couche API (FastAPI)
- API REST pour exposer les données analytiques.
- Endpoints produits + endpoints statistiques.
- Documentation Swagger native pour test rapide et communication technique.

### 4.4 Couche Restitution (Streamlit)
- Dashboard interactif avec filtres.
- Double source de données: SQLite ou API.
- Thèmes clair/sombre et visualisations métier.


## 5) Structure du projet
```text
02_analysis.ipynb
02_api.ipynb
02_create_database.ipynb
02_enrich_with_api.ipynb
02_etl_pipeline.ipynb
02_generate_data.ipynb
07_dashboard.ipynb
02_api.py
06_api.py
07_dashboard.py
README.md
requirements.txt
data/
	clean/
	raw/
sql/
outputs/
```


## 6) Explication détaillée des composants

### 6.1 ETL et qualité de données
But:
- fiabiliser les données avant calcul KPI,
- garantir la reproductibilité.

Choix méthodologiques:
- normalisation des dates,
- typage des montants,
- filtres sur statut `completed` pour les revenus,
- jointures explicites pour éviter les surcomptages.

Pourquoi c'est important:
Un dashboard est seulement aussi fiable que sa couche de préparation. Une mauvaise jointure peut fausser un KPI clé (ex: clients actifs).


### 6.2 API FastAPI
But:
- rendre les analyses consommables par une interface web ou un service externe.

Endpoints principaux:
- `GET /products`
- `GET /products/{id}`
- `GET /stats/revenue`
- `GET /stats/top-customers?limit=10`
- `GET /stats/top-products?limit=10`

Pourquoi ce design:
- séparation claire entre données transactionnelles et données agrégées,
- réutilisation du backend analytique,
- meilleure scalabilité qu'une logique embarquée uniquement dans le front.


### 6.3 Dashboard Streamlit
But:
- offrir un support de pilotage compréhensible immédiatement.

Fonctionnalités:
- source dynamique SQLite/API,
- KPI de synthèse,
- graphiques mensuels/catégories/top clients,
- filtres métier (devise, mois, catégorie, top N),
- rendu lisible en contexte de démonstration.

Pourquoi cette approche:
- rapidité de prototypage,
- excellente lisibilité pour des profils non techniques,
- itération visuelle rapide avec validation des besoins.


## 7) KPI et logique de calcul

### 7.1 Revenue total
Somme des montants de commandes validées (`completed`).

### 7.2 Panier moyen
`revenue_total / nombre_commandes_completed`.

### 7.3 Revenue par mois
Agrégation temporelle mensuelle pour suivre la tendance.

### 7.4 Revenue par catégorie
Agrégation par famille produit pour orienter la stratégie commerciale.

### 7.5 Top clients
Classement des clients selon la dépense cumulée.


## 8) Vérification par mois (contrôle analytique)
Cette partie a été intégrée pour s'assurer qu'un KPI affiché est cohérent avec la réalité métier:

1. Vérification du volume de commandes par mois.
2. Contrôle de la somme mensuelle vs total global.
3. Validation de la continuité temporelle (absence de trous inattendus).
4. Comparaison des tendances entre source SQLite et source API.

Intérêt recruteur:
Cette démarche montre une posture analytique mature: ne pas seulement afficher des graphiques, mais valider la qualité des signaux décisionnels.


## 9) Outils et stack technique
- Python
- Pandas
- SQLite
- FastAPI
- Uvicorn
- Streamlit
- Matplotlib
- SQL


## 10) Démarrage rapide

### 10.1 Installation
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

### 10.2 Lancer l'API
```bash
python 06_api.py
```
Puis ouvrir:
- `http://127.0.0.1:8000/docs`

### 10.3 Lancer le dashboard
```bash
streamlit run 07_dashboard.py
```


## 11) Compétences acquises et démontrées

### 11.1 Data Engineering
- Structuration ETL de bout en bout.
- Contrôle qualité des jeux de données.
- Gestion des transformations reproductibles.

### 11.2 Data Analysis
- Construction d'indicateurs métier pertinents.
- Validation des KPI et interprétation.
- Lecture critique de la cohérence des résultats.

### 11.3 Backend/API
- Conception d'API REST orientée usage analytique.
- Documentation Swagger et tests d'endpoint.
- Gestion des formats de payload pour intégration front.

### 11.4 Data Visualization
- Conception de tableaux de bord clairs et actionnables.
- Ajustements de lisibilité (axes, annotations, thèmes, couleurs).
- UX orientée compréhension métier.

### 11.5 Méthodologie projet
- Débogage progressif et traçable.
- Correction de régressions.
- Itération courte basée sur feedback utilisateur.


## 12) Utilisation de l'IA dans ce projet
L'IA a été utilisée comme assistant de productivité sur des tâches ciblées:
- accélération de rédaction de blocs de code répétitifs,
- proposition de correctifs sur parsing API et rendu visuel,
- aide à la structuration de certaines étapes de documentation.

Approche appliquée:
1. Génération assistée sur des briques techniques.
2. Relecture humaine systématique.
3. Vérification fonctionnelle (tests endpoint, rendu dashboard, cohérence KPI).
4. Ajustements manuels selon les besoins métier.

Important:
La logique analytique, les choix d'architecture et la validation des résultats sont restés pilotés manuellement.


## 13) Ce qu'un recruteur peut retenir
Ce projet démontre la capacité à:
- livrer une solution Data complète, opérationnelle et présentable,
- relier technique et impact métier,
- exposer des données de manière propre (API) et exploitable (dashboard),
- travailler avec une démarche qualité sur les indicateurs.


## 14) Évolutions possibles
- Ajout de tests unitaires automatisés (API + transformations).
- Déploiement cloud (API + dashboard).
- Historisation des KPI et alerting.
- Segmentation client avancée et scoring.


## 15) Auteur
Projet réalisé dans une logique professionnalisante Data / BI, avec focus sur la valeur métier, la clarté technique et la qualité de restitution.

