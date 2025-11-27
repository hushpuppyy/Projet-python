from datetime import datetime
from Document import RedditDocument, ArxivDocument

class DocumentFactory:

    @staticmethod
    def reddit_from_post(post) -> RedditDocument:
        """Construit un RedditDocument à partir d'un objet post PRAW."""
        titre = post.title or "(Sans titre)"
        auteur = str(post.author) if post.author else "Inconnu"
        date = datetime.fromtimestamp(post.created_utc)
        url = f"https://www.reddit.com{post.permalink}"
        texte = post.selftext or ""
        nb_comments = getattr(post, "num_comments", 0)
        return RedditDocument(titre, auteur, date, url, texte, nb_comments=nb_comments)

    @staticmethod
    def arxiv_from_entry(e) -> ArxivDocument:
        """Construit un ArxivDocument à partir d'une entrée XML ArXiv (xmltodict)."""
        titre = (e.get("title") or "").strip()
        titre = " ".join(titre.split())

        authors = e.get("author", [])
        if isinstance(authors, list):
            authors_names = [a.get("name", "").strip() for a in authors if isinstance(a, dict)]
            auteur_principal = authors_names[0] if authors_names else "Inconnu"
            coauthors = authors_names[1:]
        elif isinstance(authors, dict):
            auteur_principal = authors.get("name", "Inconnu")
            coauthors = []
        else:
            auteur_principal = "Inconnu"
            coauthors = []

        published = e.get("published", "")
        try:
            date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except Exception:
            date = published

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

        summary = e.get("summary", "") or ""
        summary = " ".join(summary.split())

        return ArxivDocument(titre, auteur_principal, date, url, summary, coauthors=coauthors)