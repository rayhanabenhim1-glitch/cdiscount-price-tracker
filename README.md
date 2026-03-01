# 🛍️ Cdiscount Price Analyzer & Tracker

## 📖 Project Overview / Présentation du Projet
Ce projet est une application complète de **Web Scraping et d'Analyse de Données** conçue pour automatiser la surveillance des prix sur Cdiscount. Développé dans le cadre du cours "Techniques de Programmation II", cet outil démontre l'application pratique des concepts de web scraping éthique, d'automatisation et de développement d'interfaces graphiques.

L'objectif est de permettre à un utilisateur de rechercher un produit via une interface graphique (GUI), de récupérer les meilleures offres en temps réel, et d'être alerté automatiquement en cas de baisse de prix par rapport aux recherches précédentes.

---

## ⚖️ Legal & Ethical Compliance
- ✅ **Respect de robots.txt** : Vérification systématique avant chaque requête via `urllib.robotparser`
- ✅ **Délais entre requêtes** : 2-5 secondes (crawl delay) pour ne pas surcharger les serveurs
- ✅ **Headless mode** : Navigation invisible avec Selenium pour minimiser l'impact
- ✅ **User-Agent identifié** : Transparence sur l'identité du bot
- ✅ **Rate limiting** : Limitation du nombre de pages scannées (max 2 pages, 5 produits)
- ✅ **Usage éducatif uniquement** : Projet scolaire, pas d'utilisation commerciale

---

## 🚀 Key Features / Fonctions Clés

### 1. Automation & Extraction (Selenium)
- **Scraping Dynamique :** Utilisation de Selenium en mode "Headless" pour naviguer sur Cdiscount comme un humain, gérant les contenus chargés en JavaScript.
- **Auto-Installation :** Le script détecte et installe automatiquement les bibliothèques manquantes (`selenium`, `webdriver-manager`, etc.) dès le premier lancement.
- **Gestion du Driver :** Téléchargement automatique du WebDriver Chrome approprié à la version du navigateur de l'utilisateur.
- **Cross-Platform :** Compatible Windows, macOS et Linux (fallback automatique vers Edge sur Windows).

### 2. Algorithme d'Analyse & Scoring
- **Top 3 Recommendations :** Le programme n'affiche pas juste des données brutes ; il calcule un score basé sur le prix, la note des clients et la rapidité de livraison pour proposer les 3 meilleures options.
- **Système de Scoring :**
  - Prix < 200€ : +5 points
  - Note > 4.5 : +3 points  
  - Livraison gratuite : +2 points
- **Historique Local :** Sauvegarde automatique de chaque recherche dans un fichier CSV (`data/historique_prix.csv`) pour créer une base de données de prix.

### 3. Système d'Alerte Intelligent
- **Détection de Baisse de Prix :** Comparaison instantanée entre le prix actuel et le prix le plus bas enregistré historiquement.
- **Notifications Email (SMTP Gmail) :** Envoi automatique d'un email HTML formaté à l'utilisateur si une opportunité d'achat (baisse de prix) est détectée.
- **Calcul d'économies :** Pourcentage et montant économisé affichés dans l'email.

### 4. Interface Graphique (GUI)
- Une interface intuitive construite avec **Tkinter** permettant :
  - La saisie simplifiée de la recherche
  - La configuration des paramètres email (avec stockage sécurisé dans `config.json`)
  - L'affichage clair des résultats et des logs d'exécution
  - Accès direct au dossier de données

### 5. Sécurité & Bonnes Pratiques
- **Stockage sécurisé :** Les identifiants email sont stockés dans `data/config.json` (ignoré par git)
- **Logging :** Journalisation complète dans `data/scraper.log`
- **Gestion d'erreurs :** Try/except sur toutes les opérations critiques
- **Fallbacks :** Multiples tentatives si Chrome n'est pas disponible

---


## 📂 Project Structure

## Dépendances

Les modules suivants sont indispensables et listés dans le `requirements.txt` :
- `selenium` & `webdriver-manager` (Navigation automatique)
- `beautifulsoup4` (Analyse HTML)
- `requests` (Vérification robots.txt)
- `tkinter` (Interface graphique - inclus avec Python)

## Mentions Légales

Ce projet est réalisé dans un but pédagogique uniquement. 
L'utilisation intensive du scraping peut être soumise aux conditions 
générales d'utilisation du site Cdiscount. Les auteurs ne sont pas 
responsables d'une utilisation abusive.

Le projet est organisé de manière modulaire pour faciliter la maintenance et l’extension :  
- `main.py` contient le code principal et la logique de scraping.  
- `data/` stocke l’historique des prix, les paramètres de configuration sécurisés et les logs.  
- `requirements.txt` liste toutes les dépendances nécessaires.  
- `.gitignore` protège les fichiers sensibles et temporaires.  

Cette structure permet de séparer clairement le code, les données et les configurations, tout en rendant le projet facilement réutilisable et extensible



## ⚙️ Instructions d'installation 

1. Cloner le dépôt :
git clone https://github.com/rayhanabenhim1-glitch/cdiscount-price-tracker.git

2. Aller dans le dossier du projet :
cd cdiscount-price-tracker

3. Installer les dépendances nécessaires :
pip install -r requirements.txt

4. Lancer l’application :
python main.py



## ▶️ Utilisation

Une fois l’application lancée, l’utilisateur bénéficie d’une surveillance automatique des prix :

1. Recherche instantanée d’un produit sur Cdiscount avec récupération des meilleures offres.

2. Calcul des 3 meilleures recommandations en combinant prix, note client et rapidité de livraison.

3. Comparaison avec l’historique local pour détecter les baisses de prix.

4. Envoi d’alertes email automatisées si une opportunité d’achat est détectée.

Toutes ces étapes sont totalement automatisées, sans intervention manuelle après le lancement.
Cette approche met en valeur la puissance du web scraping éthique, l’automatisation et l’analyse de données intégrée dans l’outil.




