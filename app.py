import sys
from pathlib import Path

from flask import Flask, render_template, request
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from Corpus import Corpus
from SearchEngine import SearchEngine

#Utiliser le corpus du TD7 et ne pas utiliser les discours pour n'avoir que les articles sur la cybersecurité 
corpus = Corpus.load("RedditArxiv", "corpus.tsv")

print("Nb docs (TD7) :", len(corpus.id2doc))

engine_tfidf = SearchEngine(corpus, use_tfidf=True)
engine_bm25  = SearchEngine(corpus, use_tfidf=False)

print("Taille vocab (TF-IDF) :", len(engine_tfidf.vocab))

def run_search(query: str, n: int = 10, method: str = "tfidf") -> pd.DataFrame:
    method = method.lower()
    if method == "tfidf":
        return engine_tfidf.search(query, n=n)
    elif method == "bm25":
        return engine_bm25.search(query, n=n)
    else:
        raise ValueError("Méthode inconnue : tfidf ou bm25")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "").strip()
    ui_mode = request.args.get("mode", "BM25")
    ui_source = request.args.get("source", "Toutes")
    nb_results = int(request.args.get("nb_results", 20))

    if ui_mode.upper().startswith("TF"):
        method = "tfidf"
    else:
        method = "bm25"

    source_map = {
        "Toutes": None,
        "Reddit": "reddit",
        "Arxiv": "arxiv",
    }
    source_filter = source_map.get(ui_source, None)

    results = []

    if query:
        df_res = run_search(query, n=nb_results, method=method)

        if source_filter is not None and "type" in df_res.columns:
            df_res = df_res[df_res["type"] == source_filter]

        if not df_res.empty:
            display_cols = [
                c for c in ["doc_id", "score", "type", "auteur", "titre", "url", "date"]
                if c in df_res.columns
            ]
            df_small = df_res[display_cols].copy()

            type_labels = {
                "reddit": "Reddit",
                "arxiv": "Arxiv",
            }

            results = []
            for _, row in df_small.iterrows():
                r = row.to_dict()
                r["type_label"] = type_labels.get(r.get("type"), r.get("type", "Autre"))
                results.append(r)

    nb_docs = len(corpus.id2doc)
    try:
        auteurs_uniques = len({doc.auteur for doc in corpus.id2doc.values()})
    except Exception:
        auteurs_uniques = 0

    try:
        vocab_size = len(engine_tfidf.vocab)
    except Exception:
        vocab_size = 0

    return render_template(
        "index.html",
        query=query,
        mode=ui_mode,
        source=ui_source,
        nb_results=nb_results,
        results=results,
        nb_docs=nb_docs,
        auteurs_uniques=auteurs_uniques,
        vocab_size=vocab_size,
    )

if __name__ == "__main__":
    app.run(debug=True)
