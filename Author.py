# Author.py
from typing import Dict
from Document import Document 


# production : {doc_id: Document}
class Author:
    def __init__(self, name: str):
        self.name: str = name
        self.production: Dict[int,"Document"] = {}
        self.ndoc: int = 0

    def add(self, doc_id: int, document: "Document") -> None:
        """Ajoute un document à la production de l'auteur."""
        if doc_id not in self.production:
            self.production[doc_id] = document
            self.ndoc = len(self.production)

    def total_length(self) -> int:
        """Longueur totale (en caractères) des textes produits."""
        return sum(len(doc.texte) for doc in self.production.values())

    def avg_length(self) -> float:
        """Taille moyenne (en caractères) des documents produits."""
        return self.total_length() / self.ndoc if self.ndoc else 0.0

    def __str__(self) -> str:
        return f"Auteur: {self.name} | {self.ndoc} document(s)"
