import logging
import os
import httpx
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import models
from app.repositories import embedding_repository

logger = logging.getLogger(__name__)

EMBEDDINGS_SERVICE_URL = os.getenv("EMBEDDINGS_SERVICE_URL", "http://embeddings:8000")


class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db

    def embed_text(self, text: str) -> List[float]:
        response = httpx.post(
            f"{EMBEDDINGS_SERVICE_URL}/embed",
            json={"text": text},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = httpx.post(
            f"{EMBEDDINGS_SERVICE_URL}/embed",
            json={"texts": texts},
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    def build_chunk_text(self, framework_name: str, chapter_title: str, objective) -> str:
        parts = [f"Framework: {framework_name}"]
        parts.append(f"Chapter: {chapter_title}")
        parts.append(f"Objective: {objective.title}")
        if objective.subchapter:
            parts.append(f"Subchapter: {objective.subchapter}")
        if objective.requirement_description:
            parts.append(f"Requirement: {objective.requirement_description}")
        if objective.objective_utilities:
            parts.append(f"Guidance: {objective.objective_utilities}")
        if objective.applicable_operators:
            parts.append(f"Applicable operators: {objective.applicable_operators}")
        return "\n".join(parts)

    def ingest_framework_objectives(self, framework_id) -> int:
        framework = self.db.query(models.Framework).filter(
            models.Framework.id == framework_id
        ).first()
        if not framework:
            logger.warning(f"Framework {framework_id} not found for embedding ingestion")
            return 0

        chapters = self.db.query(models.Chapters).filter(
            models.Chapters.framework_id == framework_id
        ).all()

        if not chapters:
            logger.info(f"No chapters found for framework {framework_id}")
            return 0

        # Delete existing embeddings for this framework
        embedding_repository.delete_by_framework(self.db, framework_id)

        # Build chunks
        chunks = []
        objectives_list = []
        for chapter in chapters:
            objectives = self.db.query(models.Objectives).filter(
                models.Objectives.chapter_id == chapter.id
            ).all()
            for objective in objectives:
                chunk_text = self.build_chunk_text(framework.name, chapter.title, objective)
                chunks.append(chunk_text)
                objectives_list.append(objective)

        if not chunks:
            logger.info(f"No objectives found for framework {framework.name}")
            return 0

        # Batch embed (in batches of 64 to avoid timeouts)
        batch_size = 64
        all_vectors = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            vectors = self.embed_texts(batch)
            all_vectors.extend(vectors)

        # Build embedding records
        embeddings_list = []
        for i, (objective, chunk_text, vector) in enumerate(zip(objectives_list, chunks, all_vectors)):
            embeddings_list.append(models.ObjectiveEmbedding(
                objective_id=objective.id,
                framework_id=framework_id,
                chunk_text=chunk_text,
                embedding=vector
            ))

        embedding_repository.bulk_create(self.db, embeddings_list)
        logger.info(f"Embedded {len(embeddings_list)} objectives for framework {framework.name}")
        return len(embeddings_list)

    def retrieve_relevant_objectives(
        self, query: str, org_id, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        query_vector = self.embed_text(query)
        return embedding_repository.search_similar(self.db, query_vector, org_id, top_k)
