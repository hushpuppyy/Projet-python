Projet Python – TD3 à TD10
Moteur de recherche documentaire (Reddit + Arxiv)

Ce dépôt contient l’ensemble de notre travail réalisé entre les TD3 et TD10 du module Python.
L’objectif du projet était de construire progressivement un moteur de recherche documentaire, depuis l’acquisition de données jusqu’à la construction d’une interface web fonctionnelle.

Contenu du dépôt
TD3 – Acquisition de données
Récupération d’articles via Reddit (API Pushshift)
Téléchargement de publications scientifiques via Arxiv
Prétraitement des documents
Construction du premier fichier corpus.csv

TD4 – Nettoyage et normalisation
Lemmatization / tokenisation
Suppression des stopwords
Construction d’un corpus propre exploitable pour la suite

TD5 & TD6 – Statistiques et fréquences
Calcul des fréquences TF / DF
Exploration du vocabulaire
Analyse de distribution des mots dominants

TD7 – Construction du moteur de recherche
Indexation complète du corpus (corpus.tsv)
Génération de l’index :
vocab.tsv
freq.tsv
mat_TF.npz
mat_TFxIDF.npz
Implémentation du moteur TF-IDF et BM25
Recherche textuelle fonctionnelle en console

TD8 – Interface graphique minimaliste (CLI / notebook)
Ouvrir plutot avec jupyter notebook pour une meilleur visibilté 
Construction d’une interface simple pour interroger l’index
Visualisation des résultats dans un DataFrame
Classement des scores de pertinence

TD9–10 – Interface Web avec Flask
Ouvrir plutot avec jupyter notebook pour une meilleur visibilté 
Ce TD consiste à transformer le moteur de recherche en une application web complète :
Création d’un serveur web Flask (app.py)
Intégration du moteur TF-IDF / BM25
Création d’une page HTML (index.html)
Design complet avec un fichier CSS (style.css)
  Affichage dynamique :
    titre de l’article
    auteur
    source (Reddit / Arxiv)
    score de pertinence
    lien cliquable vers le document original

  L’utilisateur peut choisir :
    le mode de recherche (TF-IDF ou BM25)
    la source (Reddit, Arxiv, ou toutes)
    le nombre de résultats affichés
    la requête textuelle dans la barre de recherche

Aller plus loin : moteur de recherche spécialisé cybersécurité
Pour aller plus loin que les TD demandés, nous avons décidé de créer un moteur de recherche thématique sur la cybersécurité, basé sur les documents collectés dans les TD précédents (Arxiv + Reddit).

L’objectif :
Créer une interface moderne qui permet :
  de taper un mot-clé (ex : malware, cybersecurity, ai security)
  de rechercher dans tous les documents scientifiques ou discussions Reddit
  d’afficher uniquement les articles pertinents
  de rendre ces articles cliquables pour accéder à la source
  de filtrer par plateforme
  d’obtenir un score de pertinence basé sur l’index du TD7
Ce moteur de recherche reprend tout le pipeline des TD et l’étend vers une utilisation réelle.

Comment tester le moteur de recherche ?
Lancer le serveur : python app.py
Ouvrir dans le navigateur :http://127.0.0.1:5000/

Entrer un mot-clé dans la barre de recherche
Explorer les résultats classés par pertinence
Cliquer sur un article pour ouvrir la source Reddit ou Arxiv
