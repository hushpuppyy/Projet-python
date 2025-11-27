# Document.py
from datetime import datetime


class Document:
    def __init__(self, titre, auteur, date, url, texte, doc_type="generic"):
        self.titre = titre
        self.auteur = auteur
        self.date = date            # datetime ou str
        self.url = url
        self.texte = texte
        self.type = doc_type        # <- important pour getType()

    # ---------- Métier commun ----------
    def getType(self) -> str:
        return self.type

    def __str__(self) -> str:
        return f"[{self.getType().upper()}] {self.titre}"

    # ---------- Sérialisation (Corpus.save / load) ----------
    def to_record(self, doc_id: int) -> dict:
        if isinstance(self.date, datetime):
            iso_date = self.date.isoformat()
        else:
            iso_date = str(self.date)

        coauthors = getattr(self, "coauthors", [])
        nb_comments = getattr(self, "nb_comments", 0)

        return {
            "id": doc_id,
            "titre": self.titre,
            "auteur": self.auteur,
            "date": iso_date,
            "url": self.url,
            "texte": self.texte,
            "type": self.getType(),
            "nb_comments": nb_comments,
            "coauthors": ", ".join(coauthors),
        }

    @staticmethod
    def from_record(rec: dict) -> "Document":
        raw = rec.get("date", "")
        date = raw
        try:
            if isinstance(raw, str) and raw:
                date = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            pass

        return Document(
            titre=rec.get("titre", ""),
            auteur=rec.get("auteur", ""),
            date=date,
            url=rec.get("url", ""),
            texte=rec.get("texte", ""),
            doc_type=rec.get("type", "generic"),
        )


# ======================================================================
# Classe fille : RedditDocument
# ======================================================================

class RedditDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, nb_comments: int = 0):
        super().__init__(titre, auteur, date, url, texte, doc_type="reddit")
        self.nb_comments = int(nb_comments)

    def get_nb_comments(self) -> int:
        return self.nb_comments

    def set_nb_comments(self, n: int) -> None:
        self.nb_comments = int(n)

    def __str__(self) -> str:
        return (
            f"[REDDIT] {self.titre} — auteur={self.auteur} "
            f"— commentaires={self.nb_comments}"
        )


# ======================================================================
# Classe fille : ArxivDocument
# ======================================================================

class ArxivDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, coauthors=None):
        super().__init__(titre, auteur, date, url, texte, doc_type="arxiv")
        self.coauthors = coauthors or []

    def get_coauthors(self):
        return self.coauthors

    def add_coauthor(self, name: str):
        if name and name not in self.coauthors:
            self.coauthors.append(name)

    def __str__(self) -> str:
        co = ", ".join(self.coauthors) if self.coauthors else "aucun co-auteur"
        return (
            f"[ARXIV] {self.titre} — auteur principal={self.auteur} "
            f"— co-auteurs={co}"
        )
