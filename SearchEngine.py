from typing import Dict, List
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from Corpus import Corpus
from Document import Document


class SearchEngine:
    def __init__(self, corpus: Corpus, use_tfidf: bool = True):
        self.corpus = corpus
        self.use_tfidf = use_tfidf

        # Vocabulaire : mot -> index de colonne
        self.vocab: Dict[str, int] = {}
        self.id2word: List[str] = []
        self.doc_ids: List[int] = []

        # Matrices
        self.mat_tf: csr_matrix | None = None
        self.mat_tfidf: csr_matrix | None = None

        # IDF + normes des docs 
        self.idf: np.ndarray | None = None
        self.doc_norms: np.ndarray | None = None

        self._build_index()

    def _build_index(self):
        print("\n=== Construction de l'index (TD7) ===")

        texts_tokens: List[List[str]] = []

        # 1) Parcourt du corpus, nettoyage, tokenisation
        for doc_id, doc in self.corpus.id2doc.items():
            self.doc_ids.append(doc_id)

            txt = self.corpus.nettoyer_texte(doc.texte)
            tokens = txt.split()
            texts_tokens.append(tokens)

            # construction du vocabulaire
            for tok in tokens:
                if tok not in self.vocab:
                    idx = len(self.vocab)
                    self.vocab[tok] = idx
                    self.id2word.append(tok)

        n_docs = len(self.doc_ids)
        n_terms = len(self.vocab)
        print(f"- Nombre de documents : {n_docs}")
        print(f"- Taille du vocabulaire : {n_terms}")

        # 2) Construction de la matrice TF 
        rows = []
        cols = []
        data = []

        for i, tokens in enumerate(texts_tokens):
            local_counts: Dict[str, int] = {}
            for tok in tokens:
                if tok in self.vocab:
                    local_counts[tok] = local_counts.get(tok, 0) + 1

            for tok, tf in local_counts.items():
                j = self.vocab[tok]
                rows.append(i)
                cols.append(j)
                data.append(tf)

        self.mat_tf = csr_matrix(
            (data, (rows, cols)),
            shape=(n_docs, n_terms),
            dtype=float,
        )

        # 3) Calcul des IDF et de la matrice TFxIDF
        df = np.asarray((self.mat_tf > 0).sum(axis=0)).ravel()
        df[df == 0] = 1  
        N = n_docs
        self.idf = np.log(N / df)  

        self.mat_tfidf = self.mat_tf.multiply(self.idf)

        # 4) Normes des documents pour la similarité cosinus
        self.doc_norms = np.sqrt(self.mat_tfidf.power(2).sum(axis=1)).A1 + 1e-12

        print("=== Index construit ===")

    def _vectorize_query(self, query: str) -> np.ndarray:
        """
        Transforme les mots-clés de la requête en un vecteur (TF-IDF)
        de dimension |vocab|.
        """
        txt = self.corpus.nettoyer_texte(query)
        tokens = txt.split()

        if not tokens:
            return np.zeros(len(self.vocab), dtype=float)

        q_vec = np.zeros(len(self.vocab), dtype=float)

        for tok in tokens:
            if tok in self.vocab:
                j = self.vocab[tok]
                q_vec[j] += 1.0

        # on applique IDF comme pour les documents
        if self.idf is not None:
            q_vec *= self.idf

        return q_vec

    def search(self, query: str, n: int = 10) -> pd.DataFrame:
        if self.mat_tfidf is None or self.doc_norms is None:
            raise RuntimeError("L'index n'a pas été construit correctement.")

        q_vec = self._vectorize_query(query)
        if not np.any(q_vec):
            print("Aucun des mots de la requête n'est dans le vocabulaire.")
            return pd.DataFrame(columns=["doc_id", "score", "titre", "auteur", "date", "type", "url"])

        q_norm = np.linalg.norm(q_vec) + 1e-12
        scores = self.mat_tfidf.dot(q_vec) 
        scores = np.asarray(scores).ravel()

        sims = scores / (self.doc_norms * q_norm)

        order = np.argsort(-sims)
        top_idx = order[:n]

        rows = []
        for idx in top_idx:
            score = sims[idx]
            if score <= 0:
                continue  

            doc_id = self.doc_ids[idx]
            doc: Document = self.corpus.id2doc[doc_id]

            rows.append({
                "doc_id": doc_id,
                "score": float(score),
                "titre": doc.titre,
                "auteur": doc.auteur,
                "date": doc.date,
                "type": getattr(doc, "type", doc.getType() if hasattr(doc, "getType") else ""),
                "url": getattr(doc, "url", ""),
            })

        df = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
        return df
