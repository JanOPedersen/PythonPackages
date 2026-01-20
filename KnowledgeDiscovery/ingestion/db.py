# ingestion/db.py
from typing import Iterable
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, JSON, Table, MetaData
)
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.engine import Engine
from ingestion.models import Paper


def get_engine(db_path: str = "papers.db") -> Engine:
    return create_engine(f"sqlite:///{db_path}", future=True)


metadata = MetaData()

papers_table = Table(
    "papers",
    metadata,
    Column("paper_id", String, primary_key=True),
    Column("doi", String, index=True),
    Column("title", Text, nullable=False),
    Column("abstract", Text),
    Column("authors", SQLITE_JSON),
    Column("year", Integer),
    Column("venue", String),
    Column("pdf_path", String),
    Column("full_text", Text),
    Column("references", SQLITE_JSON),
    Column("source", String),
    Column("user_tags", SQLITE_JSON),
    Column("projects", SQLITE_JSON),
    Column("extra", SQLITE_JSON),
)


def init_db(engine: Engine) -> None:
    metadata.create_all(engine)


def upsert_papers(engine: Engine, papers: Iterable[Paper]) -> None:
    """Simple upsert by paper_id."""
    with engine.begin() as conn:
        for p in papers:
            conn.execute(
                papers_table.insert()
                .values(
                    paper_id=p.paper_id,
                    doi=p.doi,
                    title=p.title,
                    abstract=p.abstract,
                    authors=p.authors,
                    year=p.year,
                    venue=p.venue,
                    pdf_path=p.pdf_path,
                    full_text=p.full_text,
                    references=p.references,
                    source=p.source,
                    user_tags=p.user_tags,
                    projects=p.projects,
                    extra=p.extra,
                )
                .prefix_with("OR REPLACE")
            )
