"""Utilities for product manipulation."""

import logging
from collections import Counter

logger = logging.getLogger(__name__)

__all__ = ["sort_by_candidate", "get_product_names"]


def sort_by_candidate(asns):
    """
    Sort associations by candidate.

    Parameters
    ----------
    asns : [Association[,...]]
        List of associations

    Returns
    -------
    sorted_by_candidate : [Associations[,...]]
        New list of the associations sorted.

    Notes
    -----
    The current definition of candidates allows strictly alphabetical
    sorting:
    aXXXX > cXXXX > oXXX

    If this changes, a comparison function will need be implemented
    """
    return sorted(asns, key=lambda asn: asn["asn_id"])


def get_product_names(asns):
    """
    Return product names from associations and flag duplicates.

    Parameters
    ----------
    asns : [`Association`[, ...]]
        List of associations with product entries.

    Returns
    -------
    product_names, duplicates : set(str[, ...]), [str[,...]]
        2-tuple consisting of the set of product names and the list of duplicates.
    """
    product_names = [asn["products"][0]["name"] for asn in asns]

    dups = [name for name, count in Counter(product_names).items() if count > 1]
    if dups:
        logger.debug("Duplicate product names: %s", dups)

    return set(product_names), dups
