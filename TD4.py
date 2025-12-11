import ssl
import certifi
import urllib.parse
import urllib.request
import xmltodict
import praw

from Corpus import Corpus
from DocumentFactory import DocumentFactory

def clean_text(s: str) -> str:
    return " ".join((s or "").split())

keywords = ["cybersecurity", "cyber security", "malware", "ransomware", "cyber attack"]

corpus = Corpus("CyberSec")

# 1) Reddit
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
    for post in subreddit.hot(limit=20):
        text_blob = (post.title or "") + " " + (post.selftext or "")
        if any(k.lower() in text_blob.lower() for k in keywords) and post.selftext:
            # On délègue la création du doc à la factory
            doc = DocumentFactory.reddit_from_post(post)
            corpus.add_document(doc)
            count_reddit += 1

print(f"\n[Reddit] Documents ajoutés : {count_reddit}")

# 2) ArXiv
query = " OR ".join(keywords)
params = {
    "search_query": f"all:{query}",
    "start": 0,
    "max_results": 20,  
    "sortBy": "relevance",
    "sortOrder": "descending",
}

base_url = "http://export.arxiv.org/api/query"
url = base_url + "?" + urllib.parse.urlencode(params)
print("[DEBUG] URL Arxiv utilisée :")
print(url)

ctx = ssl.create_default_context(cafile=certifi.where())
headers = {
    "User-Agent": "cybersec-scraper/1.0 (mailto:andrea.lyonnet@gmail.com)"
}
req = urllib.request.Request(url, headers=headers)

xml_data = b""
try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        xml_data = resp.read()
except Exception as e:
    print(f"[ERROR] arXiv request failed: {e}")

if not xml_data:
    print("[WARN] Aucune donnée reçue d'Arxiv (xml_data vide).")
    entries = []
else:
    print("\n[DEBUG] 200 premiers octets de la réponse Arxiv :")
    print(xml_data[:200])

    try:
        data = xmltodict.parse(xml_data)
        feed = data.get("feed", {}) or {}
        entries = feed.get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        print(f"[arXiv] Nombre d'entrées : {len(entries)}")
    except Exception as e:
        print(f"[ERROR] arXiv parse failed: {e}")
        entries = []

count_arxiv = 0
for e in entries:
    doc = DocumentFactory.arxiv_from_entry(e)
    if not doc.texte:
        continue
    corpus.add_document(doc)
    count_arxiv += 1

print(f"[arXiv] Documents ajoutés : {count_arxiv}")

print("\n=== Corpus courant ===")
print(corpus)

print("\n--- Top 7 par date ---")
corpus.show_by_date(7)

print("\n--- Top 7 par titre ---")
corpus.show_by_title(7)

corpus.save("corpus.tsv")
corpus_reloaded = Corpus.load("CyberSec(reload)", "corpus.tsv")

print("\n=== Corpus rechargé depuis corpus.tsv ===")
print(corpus_reloaded)
corpus_reloaded.show_by_title(3)

name = input("\nAuteur pour statistiques : ").strip()
if name in corpus.authors:
    aut = corpus.authors[name]
    nb_docs = aut.ndoc
    total_len = sum(len(d.texte) for d in aut.production.values())
    avg_len = total_len / nb_docs if nb_docs else 0
    print(f"\nAuteur : {name}")
    print(f"Docs : {nb_docs}")
    print(f"Taille moyenne : {avg_len:.1f} caractères")
    print("Titres :")
    for doc_id, d in aut.production.items():
        print(f" - ({doc_id}) {d.titre[:80]}")
else:
    print("Auteur inconnu dans le corpus.")

# Test 
corpus1 = Corpus("CyberSec")
corpus2 = Corpus("AutreNom")
print("\nSingleton Corpus ? :", corpus1 is corpus2)
