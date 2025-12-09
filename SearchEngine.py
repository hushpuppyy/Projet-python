# SearchEngine.py

from typing import Dict, List
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from Corpus import Corpus
from Document import Document
from tqdm.notebook import tqdm


class SearchEngine:
    """
    Moteur de recherche basé sur un objet Corpus.
    - construit le vocabulaire
    - construit la matrice Documents x Termes (TF)
    - construit la matrice TFxIDF
    - propose une méthode search(mots_cles, n) qui renvoie un DataFrame

    Deux modes de scoring possibles :
      - TF-IDF + cosinus  (par défaut)
      - BM25              (si use_tfidf=False ou method="bm25")
    """

    def __init__(self, corpus: Corpus, use_tfidf: bool = True):
        self.corpus = corpus
        self.use_tfidf = use_tfidf

        # Vocabulaire : mot -> index de colonne
        self.vocab: Dict[str, int] = {}
        self.id2word: List[str] = []

        # Liste des ids de documents dans l'ordre des lignes de la matrice
        self.doc_ids: List[int] = []

        # Matrices
        self.mat_tf: csr_matrix | None = None
        self.mat_tfidf: csr_matrix | None = None

        # IDF + normes des docs (pour le cosinus TF-IDF)
        self.idf: np.ndarray | None = None
        self.doc_norms: np.ndarray | None = None

        # Infos supplémentaires pour BM25
        self.df: np.ndarray | None = None          # document frequency
        self.doc_lengths: np.ndarray | None = None # longueur de chaque doc
        self.avg_doc_length: float | None = None   # longueur moyenne
        self.N: int = 0                            # nombre total de docs

        # Construction de l'index au moment de l'instanciation
        self._build_index()

    # ---------------------------------------------------------
    # Construction de la matrice Documents x Termes
    # ---------------------------------------------------------
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
        self.N = n_docs
        print(f"- Nombre de documents : {n_docs}")
        print(f"- Taille du vocabulaire : {n_terms}")

        # 2) Construction de la matrice TF (sparse CSR)
        rows: List[int] = []
        cols: List[int] = []
        data: List[float] = []

        for i, tokens in enumerate(texts_tokens):
            # comptage des mots dans le document i
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

        # Longueur de chaque document (somme des TF)
        self.doc_lengths = np.asarray(self.mat_tf.sum(axis=1)).ravel()
        self.avg_doc_length = float(self.doc_lengths.mean()) if n_docs > 0 else 0.0

        # 3) Calcul des IDF (TF-IDF classique) et de la matrice TFxIDF
        # df = nombre de documents contenant le mot
        self.df = np.asarray((self.mat_tf > 0).sum(axis=0)).ravel()
        self.df[self.df == 0] = 1  # sécurité

        N = n_docs
        self.idf = np.log(N / self.df)  # IDF classique

        self.mat_tfidf = self.mat_tf.multiply(self.idf)

        # 4) Normes des documents pour la similarité cosinus (mode TF-IDF)
        self.doc_norms = np.sqrt(self.mat_tfidf.power(2).sum(axis=1)).A1 + 1e-12

        print("=== Index construit ===")

    # ---------------------------------------------------------
    # Vectorisation d'une requête (TF-IDF)
    # ---------------------------------------------------------
    def _vectorize_query(self, query: str) -> np.ndarray:
        """
        Transforme les mots-clés de la requête en un vecteur (TF-IDF)
        de dimension |vocab| (utilisé pour le mode TF-IDF).
        """
        txt = self.corpus.nettoyer_texte(query)
        tokens = txt.split()

        if not tokens:
            return np.zeros(len(self.vocab), dtype=float)

        q_vec = np.zeros(len(self.vocab), dtype=float)

        # TF pour la requête
        for tok in tokens:
            if tok in self.vocab:
                j = self.vocab[tok]
                q_vec[j] += 1.0

        # on applique IDF comme pour les documents
        if self.idf is not None:
            q_vec *= self.idf

        return q_vec

    # ---------------------------------------------------------
    # Scoring BM25 (vectorisé par termes)
    # ---------------------------------------------------------
    def _bm25_scores(self, query: str, k1: float = 1.5, b: float = 0.75) -> np.ndarray:
        """
        Calcule les scores BM25 pour tous les documents du corpus
        pour une requête donnée.
        Retourne un vecteur de taille N (un score par document).
        """
        if self.mat_tf is None or self.df is None or self.doc_lengths is None or self.avg_doc_length is None:
            raise RuntimeError("L'index BM25 n'est pas disponible.")

        txt = self.corpus.nettoyer_texte(query)
        tokens = txt.split()

        # On ne garde que les termes présents dans le vocabulaire
        term_indices: List[int] = []
        for tok in tokens:
            if tok in self.vocab:
                term_indices.append(self.vocab[tok])

        if not term_indices:
            return np.zeros(self.N, dtype=float)

        scores = np.zeros(self.N, dtype=float)

        for j in term_indices:
            # tf pour ce terme dans tous les documents (colonne j)
            tf_col = self.mat_tf[:, j].toarray().ravel()

            # df et IDF BM25 pour ce terme
            df_t = self.df[j]
            idf_t = np.log(1.0 + (self.N - df_t + 0.5) / (df_t + 0.5))

            # BM25 : idf * tf * (k1+1) / (tf + k1*(1 - b + b*dl/avgdl))
            denom = tf_col + k1 * (1.0 - b + b * self.doc_lengths / (self.avg_doc_length + 1e-12))
            contrib = idf_t * (tf_col * (k1 + 1.0) / (denom + 1e-12))

            scores += contrib

        return scores

    # ---------------------------------------------------------
    # Recherche
    # ---------------------------------------------------------
    def search(self, query: str, n: int = 10, method: str | None = None) -> pd.DataFrame:
        """
        Recherche les documents les plus pertinents pour la requête.
        - query : chaîne de mots-clés
        - n     : nombre de documents à retourner
        - method: "tfidf" ou "bm25" (par défaut None => dépend de use_tfidf)

        Retourne un DataFrame pandas avec colonnes :
        [doc_id, score, titre, auteur, date, type, url]
        """

        if method is None:
            method = "tfidf" if self.use_tfidf else "bm25"

        method = method.lower()

        if method == "tfidf":
            if self.mat_tfidf is None or self.doc_norms is None:
                raise RuntimeError("L'index TF-IDF n'a pas été construit correctement.")

            q_vec = self._vectorize_query(query)
            if not np.any(q_vec):
                print("Aucun des mots de la requête n'est dans le vocabulaire.")
                return pd.DataFrame(
                    columns=["doc_id", "score", "titre", "auteur", "date", "type", "url"]
                )

            # Similarité cosinus : (d · q) / (||d|| * ||q||)
            q_norm = np.linalg.norm(q_vec) + 1e-12

            # Produit matrice (docs x termes) · vecteur (termes)
            scores = self.mat_tfidf.dot(q_vec)  # shape (n_docs,)
            scores = np.asarray(scores).ravel()

            sims = scores / (self.doc_norms * q_norm)

        elif method == "bm25":
            sims = self._bm25_scores(query)
            if not np.any(sims):
                print("Aucun des mots de la requête n'est dans le vocabulaire (BM25).")
                return pd.DataFrame(
                    columns=["doc_id", "score", "titre", "auteur", "date", "type", "url"]
                )

        else:
            raise ValueError(f"Méthode de scoring inconnue : {method}")

        # Tri décroissant des scores
        order = np.argsort(-sims)
        top_idx = order[:n]

        rows = []

        # Barre de progression sur la construction des résultats (TD8)
        for idx in tqdm(top_idx, desc="Construction des résultats"):
            score = sims[idx]
            if score <= 0:
                continue  # on ignore les scores nuls/négatifs

            doc_id = self.doc_ids[idx]
            doc: Document = self.corpus.id2doc[doc_id]

            rows.append(
                {
                    "doc_id": doc_id,
                    "score": float(score),
                    "titre": doc.titre,
                    "auteur": doc.auteur,
                    "date": doc.date,
                    "type": getattr(
                        doc, "type", doc.getType() if hasattr(doc, "getType") else ""
                    ),
                    "url": getattr(doc, "url", ""),
                }
            )

        df = (
            pd.DataFrame(rows)
            .sort_values("score", ascending=False)
            .reset_index(drop=True)
        )
        return df
