import pytest
from representation.core.core_entities import Document
from representation.metadata.content import (
    clean_abstract,
    extract_keywords,
    detect_language,
    process_content,
)


# ------------------------------------------------------------
# Abstract cleanup tests
# ------------------------------------------------------------

def test_clean_abstract():
    doc = Document(id="1", abstract="  This is an abstract.  ")
    doc = clean_abstract(doc)
    assert doc.abstract == "This is an abstract."


def test_clean_abstract_none():
    doc = Document(id="1", abstract=None)
    doc = clean_abstract(doc)
    assert doc.abstract is None


# ------------------------------------------------------------
# Keyword extraction tests
# ------------------------------------------------------------

def test_extract_keywords_basic():
    doc = Document(id="1", abstract="This paper introduces a new method for graph learning.")
    keywords = extract_keywords(doc)
    #assert "paper" not in keywords  # stopword
    assert "introduces" in keywords
    assert "method" in keywords
    assert "graph" in keywords
    assert "learning" in keywords


def test_extract_keywords_empty():
    doc = Document(id="1", abstract=None)
    keywords = extract_keywords(doc)
    assert keywords == []


def test_extract_keywords_max_limit():
    doc = Document(id="1", abstract="one two three four five six seven eight nine ten eleven twelve")
    keywords = extract_keywords(doc, max_keywords=5)
    assert len(keywords) == 5


# ------------------------------------------------------------
# Language detection tests
# ------------------------------------------------------------

def test_detect_language_english():
    doc = Document(id="1", abstract="This paper introduces a method.")
    lang = detect_language(doc)
    assert lang == "en"


def test_detect_language_none():
    doc = Document(id="1", abstract="Dies ist ein deutscher Text.")
    lang = detect_language(doc)
    assert lang is None


# ------------------------------------------------------------
# Pipeline tests
# ------------------------------------------------------------

def test_process_content_pipeline():
    doc = Document(id="1", abstract="  Something here. ")
    doc = process_content(doc)
    assert doc.abstract == "Something here."
