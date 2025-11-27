# TD6.py
# Analyse du contenu textuel

from Corpus import Corpus

# ============================================================
# Chargement du corpus (créé dans TD4)
# ============================================================

corpus = Corpus.load("CyberSec", "corpus.tsv")
print("Corpus chargé :", corpus)

# ============================================================
# PARTIE 1 : travail sur les expressions régulières
# ============================================================

# 1.1 : fonction search (dans Corpus)
motif = input("\n[PARTIE 1] Motif (regex) à chercher dans le corpus : ").strip()
if not motif:
    motif = "ransomware"  # valeur par défaut

extraits = corpus.search(motif, contexte=40)
print(f"\nNombre d'occurrences trouvées pour '{motif}' : {len(extraits)}")
print("\nQuelques extraits :")
for e in extraits[:5]:
    print("...", e)
    print("-" * 60)

# 1.2 : concordancier (DataFrame)
df_conc = corpus.concorde(motif, contexte=40)
print("\nAperçu du concordancier :")
print(df_conc.head())

df_conc.to_csv("concordancier.tsv", sep="\t", index=False, encoding="utf-8")
print("\nConcordancier sauvegardé dans 'concordancier.tsv'.")

# ============================================================
# PARTIE 2 : quelques statistiques
# ============================================================

# 2.x : stats() est implémentée dans Corpus (nettoyage, vocabulaire, tf/df)
try:
    n = int(input("\n[PARTIE 2] Combien de mots les plus fréquents afficher ? (n) : "))
except ValueError:
    n = 20

freq = corpus.stats(n=n)

print("\nAperçu du tableau freq (tf/df) :")
print(freq.head(20))

freq.to_csv("freq.tsv", sep="\t", index=False, encoding="utf-8")
print("\nTableau 'freq' sauvegardé dans 'freq.tsv'.")
