import pytest
from representation.core.core_entities import Document
from representation.enrichment.enrich_keywords import (
    extract_keywords_enriched,
    enrich_keywords,
)

# ------------------------------------------------------------
# extract_keywords_enriched tests
# ------------------------------------------------------------

def test_extract_keywords_enriched_basic():
    doc = Document(
        id="1",
        abstract="This paper introduces a new method for graph learning."
    )
    kws = extract_keywords_enriched(doc)

    # "paper" and "introduces" are stopwords
    assert "paper" not in kws
    assert "introduces" not in kws

    # expected meaningful tokens
    assert "new" in kws
    assert "graph" in kws
    assert "learning" in kws


def test_extract_keywords_enriched_deduplication():
    doc = Document(
        id="2",
        abstract="Graph graph graph learning learning models."
    )
    kws = extract_keywords_enriched(doc)

    # deduplication preserves order
    assert kws == ["graph", "learning", "models"]


def test_extract_keywords_enriched_short_tokens_removed():
    doc = Document(
        id="3",
        abstract="A B C an on to by x y z"
    )
    kws = extract_keywords_enriched(doc)

    # all tokens < 3 chars or stopwords → empty
    assert kws == []


def test_extract_keywords_enriched_max_keywords():
    doc = Document(
        id="4",
        abstract="one two three four five six seven eight nine ten eleven twelve"
    )
    kws = extract_keywords_enriched(doc, max_keywords=5)

    assert len(kws) == 5


def test_extract_keywords_enriched_empty_abstract():
    doc = Document(id="5", abstract=None)
    kws = extract_keywords_enriched(doc)
    assert kws == []


# ------------------------------------------------------------
# enrich_keywords tests
# ------------------------------------------------------------

def test_enrich_keywords_attaches_to_doc():
    doc = Document(
        id="6",
        abstract="This paper presents a model for neural text generation."
    )

    enriched = enrich_keywords(doc)

    assert hasattr(enriched, "enrichment")
    assert "keywords" in enriched.enrichment

    kws = enriched.enrichment["keywords"]

    # stopwords removed
    assert "paper" not in kws
    assert "presents" not in kws

    # meaningful tokens present
    assert "model" in kws
    assert "neural" in kws
    assert "generation" in kws


def test_enrich_keywords_creates_enrichment_dict_if_missing():
    doc = Document(id="7", abstract="Graph learning models.")
    doc.enrichment = None  # simulate missing enrichment field

    enriched = enrich_keywords(doc)

    assert isinstance(enriched.enrichment, dict)
    assert "keywords" in enriched.enrichment
