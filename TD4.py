# TD4.py
import ssl, certifi, urllib.parse, urllib.request, xmltodict, praw
from datetime import datetime

from Document import Document, RedditDocument, ArxivDocument
from Corpus import Corpus

#TD3 Modifiée
def clean_text(s: str) -> str:
    return " ".join((s or "").split())

keywords = ["cybersecurity", "cyber security", "malware", "ransomware", "cyber attack"]
corpus = Corpus("CyberSec")

#  1) Reddit 
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
            texte = clean_text(post.selftext)
            if not texte:
                continue
            titre = post.title or "(Sans titre)"
            auteur = str(post.author) if post.author else "Inconnu"
            date = datetime.fromtimestamp(post.created_utc)
            url = f"https://www.reddit.com{post.permalink}"

            doc = RedditDocument(
                titre=titre,
                auteur=auteur,
                date=date,
                url=url,
                texte=texte,
                nb_comments=post.num_comments,
                subreddit=sub
            )
            corpus.add_document(doc)

print(f"[Reddit] Documents ajoutés : {count_reddit}")

# 2) ArXiv 
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
headers = {"User-Agent": "cybersec-scraper/1.0 (mailto:ton.mail@example.com)"}
req = urllib.request.Request(url, headers=headers)

xml_data = b""
try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        xml_data = resp.read()
except Exception as e:
    print(f"[ERROR] arXiv request failed: {e}")

entries = []
if xml_data:
    data = xmltodict.parse(xml_data)
    feed = data.get("feed", {}) or {}
    entries = feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    print(f"[arXiv] Nombre d'entrées : {len(entries)}")

count_arxiv = 0
for e in entries:
    summary = clean_text(e.get("summary", ""))
    if not summary:
        continue

    titre = clean_text(e.get("title", "Sans titre"))

    # auteurs (peuvent être multiples)
    authors = e.get("author", [])
    if isinstance(authors, list):
        authors_names = [a.get("name", "").strip() for a in authors if isinstance(a, dict)]
        auteur_str = ", ".join(a for a in authors_names if a)
    elif isinstance(authors, dict):
        auteur_str = authors.get("name", "Inconnu")
    else:
        auteur_str = "Inconnu"

    # date
    published = e.get("published", "")
    try:
        date = datetime.fromisoformat(published.replace("Z", "+00:00"))
    except Exception:
        date = published  # fallback str

    # url
    url = ""
    links = e.get("link", [])
    if isinstance(links, list):
        for l in links:
            if l.get("@rel") == "alternate":
                url = l.get("@href", "")
                break
    elif isinstance(links, dict):
        url = links.get("@href", "")
    if not url:
        url = e.get("id", "")

# auteur principal = premier de la liste, le reste = co-auteurs
if authors_names:
    main_author = authors_names[0]
    coauthors = authors_names[1:]
else:
    main_author = auteur_str or "Inconnu"
    coauthors = []

doc = ArxivDocument(
    titre=titre,
    auteur=main_author,
    date=date,
    url=url,
    texte=summary,
    coauthors=coauthors
)
corpus.add_document(doc)


print(f"[arXiv] Documents ajoutés : {count_arxiv}")
print(corpus)  

# Affichages par date et par titre 
corpus.show_by_date(7)
corpus.show_by_title(7)

#  Sauvegarde / Chargement 
corpus.save("corpus.tsv")     
corpus2 = Corpus.load("CyberSec(reload)", "corpus.tsv")
print(corpus2)
corpus2.show_by_title(3)

# Statistiques Auteur 
name = input("\nAuteur pour statistiques : ").strip()
if name in corpus.authors:
    aut = corpus.authors[name]
    nb_docs = aut.ndoc
    total_len = sum(len(d.texte) for d in aut.production.values())
    avg_len = total_len / nb_docs if nb_docs else 0
    print(f"\nAuteur : {name}\nDocs : {nb_docs}\nTaille moyenne : {avg_len:.1f} caractères")
    print("Titres :")
    for doc_id, d in aut.production.items():
        print(f" - ({doc_id}) {d.titre[:80]}")
else:
    print("Auteur inconnu dans le corpus.")
