from typing import Dict, Tuple, List
from datetime import datetime, timezone
import pandas as pd

from Document import Document, ArxivDocument, RedditDocument
from Author import Author

import re
from collections import Counter

class Corpus:
    _instance = None

    def __new__(cls, nom: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, nom: str):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.nom = nom
        self.authors = {}
        self.id2doc = {}
        self._next_id = 1
        self._initialized = True
        self._fulltext = None

    @property
    def ndoc(self) -> int:
        return len(self.id2doc)

    @property
    def naut(self) -> int:
        return len(self.authors)

    def _register_author(self, author_field: str, doc_id: int, doc_obj: Document):
        if not author_field:
            return
        names = [a.strip() for a in str(author_field).split(",") if a.strip()]
        for name in names:
            if name not in self.authors:
                self.authors[name] = Author(name)
            self.authors[name].add(doc_id, doc_obj)

    def add_document(self, doc: Document, preserve_id: int = None) -> int:
        """Ajoute un Document et met à jour les auteurs. Retourne l'id utilisé."""
        if preserve_id is not None:
            doc_id = int(preserve_id)
            self._next_id = max(self._next_id, doc_id + 1)
        else:
            doc_id = self._next_id
            self._next_id += 1

        self.id2doc[doc_id] = doc
        self._register_author(doc.auteur, doc_id, doc)
        return doc_id

    def _date_key(self, doc):
        d = doc.date

        if isinstance(d, str):
            try:
                d = datetime.fromisoformat(d.replace("Z", "+00:00"))
            except Exception:
                return datetime.min

        if isinstance(d, datetime):
            if d.tzinfo is not None:
                d = d.astimezone(timezone.utc).replace(tzinfo=None)
            return d
        return datetime.min


    def show_by_date(self, n: int = 5, reverse: bool = True) -> List[Tuple[int, Document]]:
        """Affiche (et retourne) les n docs triés par date (récent d'abord par défaut)."""
        items = sorted(self.id2doc.items(), key=lambda kv: self._date_key(kv[1]), reverse=reverse)[:n]
        print(f"— {self.nom}: top {n} par date —")
        for doc_id, doc in items:
            print(f"[{doc_id}] {self._date_key(doc)} | {doc.titre[:80]} | {doc.auteur}")
        return items

    def show_by_title(self, n: int = 5) -> List[Tuple[int, Document]]:
        """Affiche (et retourne) les n docs triés par titre (A→Z)."""
        items = sorted(self.id2doc.items(), key=lambda kv: (kv[1].titre or "").lower())[:n]
        print(f"— {self.nom}: top {n} par titre —")
        for doc_id, doc in items:
            print(f"[{doc_id}] {doc.titre[:80]} | {doc.auteur}")
        return items

    def __repr__(self):
        return f"Corpus('{self.nom}', ndoc={self.ndoc}, naut={self.naut})"

    def to_dataframe(self) -> pd.DataFrame:
        rows = [doc.to_record(doc_id) for doc_id, doc in self.id2doc.items()]
        df = pd.DataFrame(rows, columns=["id", "titre", "auteur", "date", "url", "texte", "type", "coauthors"])
        df = df.sort_values("id")
        return df

    def save(self, path: str, sep: str = "\t", encoding: str = "utf-8"):
        """Sauvegarde le corpus en TSV (via pandas)."""
        df = self.to_dataframe()
        df.to_csv(path, sep=sep, index=False, encoding=encoding)

    @classmethod
    def load(cls, name: str, path: str, sep: str = "\t", encoding: str = "utf-8"):

        df = pd.read_csv(path, sep=sep, encoding=encoding)
        c = cls(name)
        for _, row in df.iterrows():
            rec = row.to_dict()
            doc_type = rec.get("type", "generic")
            coauthors_raw = rec.get("coauthors", "")
            coauthors = [a.strip() for a in str(coauthors_raw).split(",") if a.strip()]

            if doc_type == "arxiv":
                doc = ArxivDocument(
                    rec.get("titre", ""),
                    rec.get("auteur", ""),
                    rec.get("date", ""),
                    rec.get("url", ""),
                    rec.get("texte", ""),
                    coauthors=coauthors,
                )
            elif doc_type == "reddit":
                doc = RedditDocument(
                    rec.get("titre", ""),
                    rec.get("auteur", ""),
                    rec.get("date", ""),
                    rec.get("url", ""),
                    rec.get("texte", ""),
                )
            else:
                doc = Document.from_record(rec)

            c.add_document(doc, preserve_id=int(rec["id"]))
        return c
    def save_json(self, path: str, encoding: str = "utf-8"):
        self.to_dataframe().to_json(path, force_ascii=False, orient="records", indent=2)

    @classmethod
    def load_json(cls, name: str, path: str, encoding: str = "utf-8"):
        df = pd.read_json(path, orient="records")
        c = cls(name)
        for _, row in df.iterrows():
            rec = row.to_dict()
            doc = Document.from_record(rec)
            c.add_document(doc, preserve_id=int(rec["id"]))
        return c

    #   TD6 - PARTIE 1

    def _build_fulltext(self):
        """Construit une grande chaîne concaténant tous les textes (une seule fois)."""
        if self._fulltext is None:
            self._fulltext = " ".join(
                doc.texte for doc in self.id2doc.values() if doc.texte
            )

    def search(self, pattern: str, flags=re.IGNORECASE, contexte: int = 40):
        self._build_fulltext()
        texte = self._fulltext
        regex = re.compile(pattern, flags)

        extraits = []
        for m in regex.finditer(texte):
            start, end = m.span()
            left = texte[max(0, start - contexte): start]
            match = m.group(0)
            right = texte[end: end + contexte]
            extraits.append(left + match + right)

        return extraits

    def concorde(self, pattern: str, contexte: int = 40, flags=re.IGNORECASE) -> pd.DataFrame:
        self._build_fulltext()
        texte = self._fulltext
        regex = re.compile(pattern, flags)

        rows = []
        for m in regex.finditer(texte):
            start, end = m.span()
            left = texte[max(0, start - contexte): start]
            match = m.group(0)
            right = texte[end: end + contexte]
            rows.append({
                "contexte_gauche": left,
                "motif_trouve": match,
                "contexte_droit": right
            })

        df = pd.DataFrame(rows, columns=["contexte_gauche", "motif_trouve", "contexte_droit"])
        return df
    
    # PARTIE 2 : Statistiques textuelles (TD6)

    def nettoyer_texte(self, s: str) -> str:
        """Normalise du texte : minuscules, suppression ponctuation/chiffres, espaces propres."""
        if not isinstance(s, str):
            return ""
        s = s.lower()
        s = re.sub(r"[^\w\s]", " ", s)      # retire la ponctuation
        s = re.sub(r"\d+", " ", s)          # retire les chiffres
        s = re.sub(r"\s+", " ", s).strip()  # espaces propres
        return s

    def stats(self, n: int = 20) -> pd.DataFrame:
        print("\n=== STATISTIQUES TEXTE ===")

        # 1) Construire la liste nettoyée de tous les textes
        texts = [self.nettoyer_texte(doc.texte) for doc in self.id2doc.values()]

        # 2) Vocabulaire 
        vocab = set()
        for t in texts:
            vocab.update(t.split())

        print(f"Nombre total de mots distincts : {len(vocab)}")

        # 3) Compter TF 
        tf_counts = {w: 0 for w in vocab}
        for t in texts:
            for w in t.split():
                tf_counts[w] += 1

        # 4) Compter DF 
        df_counts = {w: 0 for w in vocab}
        for w in vocab:
            df_counts[w] = sum(1 for t in texts if w in t.split())

        # 5) Construction DataFrame final
        df = pd.DataFrame({
            "word": list(vocab),
            "tf": [tf_counts[w] for w in vocab],
            "df": [df_counts[w] for w in vocab],
        })

        df = df.sort_values(by="tf", ascending=False)

        print(f"\nTop {n} mots les plus fréquents :")
        print(df.head(n))

        return df
