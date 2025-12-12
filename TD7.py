
from Corpus import Corpus
from SearchEngine import SearchEngine

# 1) Chargement du corpus (généré dans TD4 / TD5 / TD6)
corpus = Corpus.load("CyberSec", "corpus.tsv")
print("Corpus chargé :", corpus)

# 2) Construction du moteur de recherche
engine = SearchEngine(corpus)

# 3) Boucle de requête
while True:
    query = input("\nEntrez quelques mots-clés (ou 'quit' pour arrêter) : ").strip()
    if not query or query.lower() in {"quit", "exit"}:
        break

    try:
        n = int(input("Combien de documents à afficher ? (n) : ").strip() or "10")
    except ValueError:
        n = 10

    results = engine.search(query, n)

    if results.empty:
        print("Aucun document trouvé.")
    else:
        print("\n=== Meilleurs résultats ===")
        cols = ["doc_id", "score", "type", "titre", "auteur"]
        print(results[cols].head(n).to_string(index=False))
        results.to_csv("resultats_recherche.tsv", sep="\t", index=False, encoding="utf-8")
        print("\nRésultats détaillés sauvegardés dans resultats_recherche.tsv")
