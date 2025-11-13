# Document.py
from datetime import datetime

class Document:
    def __init__(self, titre, auteur, date, url, texte):
        self.titre = titre
        self.auteur = auteur
        self.date = date          # datetime ou str
        self.url = url
        self.texte = texte
        self.type = "reddit"

    def getType(self): 
        return self.type

    def __str__(self):
        return f"[{self.getType().upper()}] {self.titre}"

    def show(self):
        print("===== Document =====")
        print(f"Titre : {self.titre}")
        print(f"Auteur : {self.auteur}")
        print(f"Date : {self.date}")
        print(f"URL  : {self.url}")
        print(f"Texte: {self.texte[:500]}{'...' if len(self.texte) > 500 else ''}")
        print("====================")

    def __str__(self):
        return f"{self.titre} ({self.date})"

    #   POUR LA SAUVEGARDE CSV / TSV (nécessaire au TD4)
    def to_record(self, doc_id: int) -> dict:
        """Transforme un Document en dict pour DataFrame."""
        iso_date = self.date.isoformat() if isinstance(self.date, datetime) else str(self.date)
        return {
            "id": doc_id,
            "titre": self.titre,
            "auteur": self.auteur,
            "date": iso_date,
            "url": self.url,
            "texte": self.texte,
        }

    @staticmethod
    def from_record(rec: dict):
        """Recrée un Document depuis un dict (DataFrame)."""
        raw_date = rec.get("date", "")
        date = raw_date

        try:
            if isinstance(raw_date, str) and raw_date:
                date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except Exception:
            pass

        return Document(
            titre=rec.get("titre", ""),
            auteur=rec.get("auteur", ""),
            date=date,
            url=rec.get("url", ""),
            texte=rec.get("texte", ""),
            doc_type=rec.get("type", "")
        )

#TD5 
class RedditDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, nb_comments=0, subreddit=None):
        # on appelle le constructeur de la classe mère
        super().__init__(titre, auteur, date, url, texte)
        # attributs spécifiques à Reddit
        self.nb_comments = nb_comments
        self.subreddit = subreddit

    # accesseurs / mutateurs
    def get_nb_comments(self):
        return self.nb_comments

    def set_nb_comments(self, n):
        self.nb_comments = n

    def __str__(self):
        return f"[Reddit] {self.titre} ({self.subreddit}) - {self.nb_comments} commentaires"


class ArxivDocument(Document):
    def __init__(self, titre, auteur, date, url, texte, coauthors=None):
        super().__init__(titre, auteur, date, url, texte)
        # coauthors : liste des autres auteurs (co-auteurs)
        self.type = "arxiv"
        self.coauthors = coauthors if coauthors else []

    # accesseurs / mutateurs
    def get_coauthors(self):
        return self.coauthors

    def set_coauthors(self, coauthors_list):
        self.coauthors = list(coauthors_list)

    def __str__(self):
        if self.coauthors:
            co = ", ".join(self.coauthors)
            return f"[ArXiv] {self.titre} – auteur principal: {self.auteur}, co-auteurs: {co}"
        else:
            return f"[ArXiv] {self.titre} – auteur: {self.auteur}"