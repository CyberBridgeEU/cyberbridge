import logging
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import models

logger = logging.getLogger(__name__)


def delete_by_framework(db: Session, framework_id):
    db.query(models.ObjectiveEmbedding).filter(
        models.ObjectiveEmbedding.framework_id == framework_id
    ).delete()
    db.flush()


def bulk_create(db: Session, embeddings_list: List[models.ObjectiveEmbedding]):
    db.bulk_save_objects(embeddings_list)
    db.commit()


def search_similar(
    db: Session, query_vector: List[float], org_id, top_k: int = 5
) -> List[Tuple[str, float]]:
    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
    sql = text("""
        SELECT oe.chunk_text, oe.embedding <=> :query_vec AS distance
        FROM objective_embeddings oe
        JOIN frameworks f ON f.id = oe.framework_id
        WHERE f.organisation_id = :org_id
        ORDER BY distance ASC
        LIMIT :top_k
    """)
    results = db.execute(sql, {
        "query_vec": vector_str,
        "org_id": str(org_id),
        "top_k": top_k
    }).fetchall()
    return [(row[0], row[1]) for row in results]


def get_counts_by_org(db: Session, org_id) -> dict:
    sql = text("""
        SELECT f.name,
               COUNT(DISTINCT o.id) AS total_objectives,
               COUNT(DISTINCT oe.id) AS embedded
        FROM frameworks f
        LEFT JOIN chapters c ON c.framework_id = f.id
        LEFT JOIN objectives o ON o.chapter_id = c.id
        LEFT JOIN objective_embeddings oe ON oe.framework_id = f.id
        WHERE f.organisation_id = :org_id
        GROUP BY f.name
        ORDER BY f.name
    """)
    results = db.execute(sql, {"org_id": str(org_id)}).fetchall()
    return {
        row[0]: {"total_objectives": row[1], "embedded": row[2]}
        for row in results
    }
