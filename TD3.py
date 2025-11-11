import os
import ssl
import certifi
import urllib.parse
import urllib.request
import xmltodict
import praw
import pandas as pd

#PARTIE 1 

docs = []  # contiendra UNIQUEMENT des dicts {"text": ..., "origin": ...}
keywords = ["cybersecurity", "cyber security", "malware", "ransomware", "cyber attack"]

def clean_text(s: str) -> str:
    return " ".join((s or "").split())

# Reddit 
reddit = praw.Reddit(
    client_id="snh42z2qlcdumEuWm0DLFQ",
    client_secret="rywmqYg_XNcu9k8cQlOKjOU-wyyJzw",
    user_agent="Cybersecurity"
)

subreddits_list = ["cybersecurity", "hacking", "netsec", "technology"]
count_reddit = 0

for sub in subreddits_list:
    subreddit = reddit.subreddit(sub)
    print(f"\n--- Subreddit : {sub} ---")
    try:
        for post in subreddit.hot(limit=20):
            text_blob = (post.title or "") + " " + (post.selftext or "")
            if any(k.lower() in text_blob.lower() for k in keywords):
                if post.selftext:
                    texte = clean_text(post.selftext)
                    if texte:
                        docs.append({"text": texte, "origin": "reddit"})
                        count_reddit += 1
    except Exception as e:
        print(f"[WARN] Reddit '{sub}': {e}")

print(f"\n[Reddit] Nombre de posts textuels ajoutés : {count_reddit}")

# ArXiv 
query = " OR ".join(keywords)
params = {
    "search_query": f"all:{query}",
    "start": 0,
    "max_results": 50,
    "sortBy": "relevance",
    "sortOrder": "descending",
}
base_url = "https://export.arxiv.org/api/query"
url = base_url + "?" + urllib.parse.urlencode(params)

ctx = ssl.create_default_context(cafile=certifi.where())
headers = {"User-Agent": "cybersec-scraper/1.0 (mailto:andrea.lyonnet@gmail.com)"}
req = urllib.request.Request(url, headers=headers)

xml_data = b""
try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        xml_data = resp.read()
except Exception as e:
    print(f"[ERROR] arXiv request failed: {e}")

entries = []
if xml_data:
    try:
        data = xmltodict.parse(xml_data)
        feed = data.get("feed", {}) or {}
        entries = feed.get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        print(f"[arXiv] Nombre d'entrées : {len(entries)}")
    except Exception as e:
        print(f"[ERROR] arXiv parse failed: {e}")

if entries:
    sample_keys = list(entries[0].keys())
    print("\nChamps disponibles sur une entrée ArXiv :")
    for k in sample_keys:
        print(" -", k)
    print("\nChamp textuel principal : 'summary'")

count_arxiv = 0
for e in entries:
    summary = clean_text(e.get("summary", ""))
    if summary:
        docs.append({"text": summary, "origin": "arxiv"})
        count_arxiv += 1

print(f"\n[arXiv] Docs textuels ajoutés : {count_arxiv}")

# Dé-duplication par (text, origin)
seen = set()
uniq = []
for d in docs:
    key = (d["text"], d["origin"])
    if key not in seen:
        uniq.append(d)
        seen.add(key)
docs = uniq

print(f"\nTotal de documents dans docs : {len(docs)}")
for i, d in enumerate(docs[:5], start=1):
    print(f"\n--- Doc {i} ({d['origin']}) ---\n{d['text'][:500]}...")

# Vue textuelle brute (
with open("docs.txt", "w", encoding="utf-8") as f:
    for i, d in enumerate(docs, start=1):
        f.write(f"--- Doc {i} ({d['origin']}) ---\n{d['text']}\n\n")
print("Écrit dans docs.txt")

# PARTIE 2 

df = pd.DataFrame(docs, columns=["text", "origin"])
df.insert(0, "id", range(1, len(df) + 1))

out_path = "corpus.csv"  # TSV demandé
df.to_csv(out_path, sep="\t", index=False, encoding="utf-8")
print(f"✅ Sauvegardé dans {out_path}")

# Rechargement sans API
in_path = "corpus.csv"
df = pd.read_csv(in_path, sep="\t", encoding="utf-8")
docs = df[["text", "origin"]].to_dict(orient="records")
print(f"✅ Chargé {len(df)} lignes depuis {in_path}")


#PARTIE 3

nb_docs = len(docs)
print(f"Taille du corpus : {nb_docs} documents")

print("\nNombre de mots et de phrases par document :")
for i, d in enumerate(docs[:5], start=1):  # affiche seulement les 5 premiers pour lisibilité
    texte = d["text"]
    nb_mots = len(texte.split(" "))
    nb_phrases = len([p for p in texte.split(".") if p.strip() != ""])
    print(f" - Doc {i}: {nb_mots} mots, {nb_phrases} phrases")

avant = len(docs)
docs = [d for d in docs if len(d["text"]) >= 20]
apres = len(docs)
print(f"\n Documents supprimés : {avant - apres} | Restants : {apres}")

# Création d’une seule chaîne contenant tout le corpus
corpus_str = " ".join(d["text"] for d in docs)
print(f"\nLongueur totale de la chaîne fusionnée : {len(corpus_str)} caractères")

# sauvegarde dans un fichier texte pour la suite
with open("corpus_total.txt", "w", encoding="utf-8") as f:
    f.write(corpus_str)
print("✅ Chaîne complète sauvegardée dans corpus_total.txt")