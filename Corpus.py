# Corpus.py
from typing import Dict, Tuple, List
from datetime import datetime, timezone
import pandas as pd

from Document import Document, ArxivDocument, RedditDocument
from Author import Author

class Corpus:
    def __init__(self, nom: str):
        self.nom = nom
        self.authors: Dict[str, Author] = {}
        self.id2doc: Dict[int, Document] = {}
        self._next_id = 1  # id auto-incrément

    # ---- Propriétés pratiques ----
    @property
    def ndoc(self) -> int:
        return len(self.id2doc)

    @property
    def naut(self) -> int:
        return len(self.authors)

    # ---- Ajout / Indexation ----
    def _register_author(self, author_field: str, doc_id: int, doc_obj: Document):
        if not author_field:
            return
        # Gère les auteurs multiples "A, B, C"
        names = [a.strip() for a in str(author_field).split(",") if a.strip()]
        for name in names:
            if name not in self.authors:
                self.authors[name] = Author(name)
            self.authors[name].add(doc_id, doc_obj)

    def add_document(self, doc: Document, preserve_id: int = None) -> int:
        """Ajoute un Document et met à jour les auteurs. Retourne l'id utilisé."""
        if preserve_id is not None:
            doc_id = int(preserve_id)
            # Maintient l'auto-incrément correct
            self._next_id = max(self._next_id, doc_id + 1)
        else:
            doc_id = self._next_id
            self._next_id += 1

        self.id2doc[doc_id] = doc
        self._register_author(doc.auteur, doc_id, doc)
        return doc_id

    # ---- Affichages triés ----

    def _date_key(self, doc):
        d = doc.date

        # Si c'est une chaîne, on essaye de parser
        if isinstance(d, str):
            try:
                d = datetime.fromisoformat(d.replace("Z", "+00:00"))
            except Exception:
                return datetime.min

        if isinstance(d, datetime):
            # On convertit TOUT en datetime "naïf" en UTC
            if d.tzinfo is not None:
                d = d.astimezone(timezone.utc).replace(tzinfo=None)
            return d

        # Si on n'arrive vraiment pas, on renvoie une date très basse
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

    # ---- Sauvegarde / Chargement via DataFrame (TSV) ----
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

    # ---- (Optionnel) autres formats ----
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
