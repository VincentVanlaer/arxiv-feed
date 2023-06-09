"""Classes derived from the Feedgen extension classes."""
from typing import Dict, List, Optional

from lxml import etree
from lxml.etree import Element
from flask import current_app
from feedgen.ext.base import BaseEntryExtension, BaseExtension

from feed.domain import Author, Media


class ArxivExtension(BaseExtension):
    """Extension of the Feedgen class to allow us to change its behavior."""

    def extend_atom(self: BaseExtension, atom_feed: Element) -> Element:
        """Allow the extension to modify the initial feed tree for Atom.

        Parameters
        ----------
        atom_feed : Element
            The feed's root element.

        Returns
        -------
        atom_feed : Element
            The feed's root element.
        """
        return atom_feed

    def extend_rss(self: BaseExtension, rss_feed: Element) -> Element:
        """Allow the extension to modify the initial feed tree for RSS.

        Parameters
        ----------
        rss_feed : Element
            The feed's root element.

        Returns
        -------
        rss_feed : Element
            The feed's root element.
        """
        return rss_feed

    def extend_ns(self: BaseExtension) -> Dict[str, str]:
        """
        Define the feed's namespaces.

        Returns
        -------
        namespaces : Dict[str, str]
            Definitions of the "arxiv" namespaces.
        """
        return {
            "arxiv": "http://arxiv.org/schemas/atom",
            "content": "http://purl.org/rss/1.0/modules/content/",
            "taxo": "http://purl.org/rss/1.0/modules/taxonomy/",
            "syn": "http://purl.org/rss/1.0/modules/syndication/",
            "admin": "http://webns.net/mvcb/",
            "media": "http://search.yahoo.com/mrss",
        }


class ArxivAtomExtension(BaseEntryExtension):
    """Atom only extension."""

    def extend_ns(self: BaseExtension) -> Dict[str, str]:
        """
        Define the feed's namespaces.

        Returns
        -------
        namespaces : Dict[str, str]
            Definitions of the "arxiv" namespaces.
        """
        return {
            "arxiv": "http://arxiv.org/schemas/atom",
        }


class ArxivEntryExtension(BaseEntryExtension):
    """Extension of the Entry class to allow us to change its behavior."""

    def __init__(self: BaseEntryExtension):
        """Initialize the member values to all be empty."""
        self.__arxiv_authors: List[Author] = []
        self.__arxiv_media: List[Media] = []
        self.__arxiv_comment: Optional[str] = None
        self.__arxiv_primary_category: Optional[str] = None
        self.__arxiv_doi: Optional[dict] = None
        self.__arxiv_affiliation: Optional[str] = None
        self.__arxiv_journal_ref: Optional[str] = None
        self.__arxiv_affiliations: Dict = {}

    def __add_media(self, entry: Element) -> None:
        for media in self.__arxiv_media:
            group = etree.SubElement(
                entry, "{http://search.yahoo.com/mrss}group"
            )
            title = etree.SubElement(
                group, "{http://search.yahoo.com/mrss}title"
            )
            title.text = media.title
            etree.SubElement(
                group,
                "{http://search.yahoo.com/mrss}content",
                attrib={"url": media.url, "type": media.type},
            )

    def extend_atom(self, entry: Element) -> Element:
        """
        Allow the extension to modify the entry element for Atom serialization.

        Parameters
        ----------
        entry : Element
            The FeedEntry to modify.

        Returns
        -------
        entry : Element
            The modified entry.

        """
        if self.__arxiv_comment:
            comment_element = etree.SubElement(
                entry, "{http://arxiv.org/schemas/atom}comment"
            )
            comment_element.text = self.__arxiv_comment

        if self.__arxiv_primary_category:
            etree.SubElement(
                entry,
                "{http://arxiv.org/schemas/atom}primary_category",
                attrib=self.__arxiv_primary_category,
            )

        if self.__arxiv_journal_ref:
            journal_ref_element = etree.SubElement(
                entry, "{http://arxiv.org/schemas/atom}journal_ref"
            )
            journal_ref_element.text = self.__arxiv_journal_ref

        if self.__arxiv_doi:
            for doi in self.__arxiv_doi:
                doi_element = etree.SubElement(
                    entry, "{http://arxiv.org/schemas/atom}doi"
                )
                doi_element.text = doi

        # Check each of the entry's author nodes
        for entry_child in entry:
            if entry_child.tag == "author":
                author = entry_child
                for author_child in author:
                    # If the author's name is in the affiliation dictionary,
                    # add Elements for all of its affiliations.
                    if author_child.tag == "name":
                        name = author_child.text
                        affiliations = self.__arxiv_affiliations.get(name, [])
                        for affiliation in affiliations:
                            element = etree.SubElement(
                                author,
                                "{http://arxiv.org/schemas/atom}affiliation",
                            )
                            element.text = affiliation

        self.__add_media(entry=entry)

        return entry

    def extend_rss(self, entry: Element) -> Element:
        """Allow the extension to modify the entry element for RSS.

        Parameters
        ----------
        entry : Element
            The FeedEntry to modify.

        Returns
        -------
        entry : Element
            The modified entry.

        """
        base_server: str = current_app.config["BASE_SERVER"]

        for entry_child in entry:
            if entry_child.tag == "description":
                description = "<p>Authors: "
                first = True
                for author in self.__arxiv_authors:
                    if first:
                        first = False
                    else:
                        description += ", "
                    name = (
                        f"{author.last_name},"
                        f"+{author.initials.replace(' ', '+')}"
                    )
                    description += (
                        f'<a href="http://{base_server}/search/?query={name}&'
                        f'searchtype=author">{author.full_name}</a>'
                    )
                description += f"</p><p>{entry_child.text}</p>"

                entry_child.text = description

        self.__add_media(entry=entry)

        return entry

    def author(self, author: Author) -> None:
        """Add an author value to this entry.

        Parameters
        ----------
        author : Author
            Paper author.
        """
        self.__arxiv_authors.append(author)

    def media(self, media: Media) -> None:
        """Add a media item.

        Parameters
        ----------
        media: Dict[str, str]
            Dictionary with url and type attributes.
        """
        self.__arxiv_media.append(media)

    def comment(self, text: str) -> None:
        """Assign the comment value to this entry.

        Parameters
        ----------
        text : str
            The new comment text.

        """
        self.__arxiv_comment = text

    def primary_category(self, text: str) -> None:
        """Assign the primary_category value to this entry.

        Parameters
        ----------
        text : str
            The new primary_category name.
        """
        self.__arxiv_primary_category = text

    def journal_ref(self, text: str) -> None:
        """Assign the journal_ref value to this entry.

        Parameters
        ----------
        text : str
            The new journal_ref value.
        """
        self.__arxiv_journal_ref = text

    def doi(self, doi_list: Dict[str, str]) -> None:
        """Assign the set of DOI definitions for this entry.

        Parameters
        ----------
        doi_list : Dict[str, str]
            A dictionary of DOI assignments.

        """
        self.__arxiv_doi = doi_list

    def affiliation(self, full_name: str, affiliations: List[str]) -> None:
        """Assign an affiliation for one author of this entry.

        Parameters
        ----------
        full_name : str
            An author's full name.
        affiliations : List[str]
            The code for the author's affiliated institution.
        """
        self.__arxiv_affiliations[full_name] = affiliations
