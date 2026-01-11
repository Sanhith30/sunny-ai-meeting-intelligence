"""
Meeting Memory (RAG System) Module
Stores and retrieves meeting information using vector embeddings.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MemoryDocument:
    """A document stored in meeting memory."""
    id: str
    meeting_id: int
    content: str
    doc_type: str  # transcript, summary, decision, action_item
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None


@dataclass
class SearchResult:
    """A search result from memory."""
    document: MemoryDocument
    score: float
    snippet: str


class MeetingMemory:
    """RAG-based meeting memory system using ChromaDB."""

    def __init__(self, config: dict):
        adv_config = config.get("advanced_features", {})
        self.enabled = adv_config.get("rag_memory_enabled", True)
        self.persist_dir = Path(adv_config.get("memory_persist_dir", "./data/memory"))
        self.collection_name = adv_config.get("memory_collection", "meeting_memory")
        
        self._client = None
        self._collection = None
        self._embedding_model = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the memory system."""
        if not self.enabled:
            logger.info("Meeting memory is disabled")
            return False

        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create persist directory
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Sunny AI Meeting Memory"}
            )
            
            # Try to load embedding model
            await self._load_embedding_model()
            
            self._initialized = True
            logger.info(f"Meeting memory initialized: {self._collection.count()} documents")
            return True
            
        except ImportError:
            logger.warning("ChromaDB not installed. Meeting memory disabled.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize meeting memory: {e}")
            return False

    async def _load_embedding_model(self) -> None:
        """Load sentence transformer for embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded")
        except ImportError:
            logger.warning("sentence-transformers not installed, using default embeddings")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        if self._embedding_model:
            embeddings = self._embedding_model.encode(texts)
            return embeddings.tolist()
        return None

    async def store_meeting(
        self,
        meeting_id: int,
        transcript: str,
        summary: Any = None,
        decisions: List[str] = None,
        action_items: List[Any] = None,
        metadata: Dict[str, Any] = None
    ) -> int:
        """Store meeting data in memory."""
        if not self._initialized:
            await self.initialize()
            if not self._initialized:
                return 0

        logger.info(f"Storing meeting {meeting_id} in memory")
        
        documents = []
        ids = []
        metadatas = []
        
        base_metadata = {
            "meeting_id": meeting_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }

        # Store transcript chunks
        if transcript:
            chunks = self._chunk_text(transcript, chunk_size=500, overlap=50)
            for i, chunk in enumerate(chunks):
                doc_id = f"meeting_{meeting_id}_transcript_{i}"
                documents.append(chunk)
                ids.append(doc_id)
                metadatas.append({
                    **base_metadata,
                    "doc_type": "transcript",
                    "chunk_index": i
                })

        # Store summary
        if summary and hasattr(summary, 'executive_summary'):
            doc_id = f"meeting_{meeting_id}_summary"
            documents.append(summary.executive_summary)
            ids.append(doc_id)
            metadatas.append({
                **base_metadata,
                "doc_type": "summary"
            })
            
            # Store key points
            if hasattr(summary, 'key_discussion_points'):
                for i, point in enumerate(summary.key_discussion_points):
                    doc_id = f"meeting_{meeting_id}_keypoint_{i}"
                    documents.append(point)
                    ids.append(doc_id)
                    metadatas.append({
                        **base_metadata,
                        "doc_type": "key_point"
                    })

        # Store decisions
        if decisions:
            for i, decision in enumerate(decisions):
                doc_id = f"meeting_{meeting_id}_decision_{i}"
                documents.append(decision)
                ids.append(doc_id)
                metadatas.append({
                    **base_metadata,
                    "doc_type": "decision"
                })

        # Store action items
        if action_items:
            for i, item in enumerate(action_items):
                task = item.task if hasattr(item, 'task') else str(item)
                owner = item.owner if hasattr(item, 'owner') else None
                
                doc_id = f"meeting_{meeting_id}_action_{i}"
                content = f"Action Item: {task}"
                if owner:
                    content += f" (Assigned to: {owner})"
                
                documents.append(content)
                ids.append(doc_id)
                metadatas.append({
                    **base_metadata,
                    "doc_type": "action_item",
                    "owner": owner
                })

        # Add to collection
        if documents:
            embeddings = self._get_embeddings(documents)
            
            if embeddings:
                self._collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
            else:
                self._collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
            
            logger.info(f"Stored {len(documents)} documents for meeting {meeting_id}")

        return len(documents)

    async def search(
        self,
        query: str,
        n_results: int = 5,
        doc_type: Optional[str] = None,
        meeting_id: Optional[int] = None
    ) -> List[SearchResult]:
        """Search meeting memory."""
        if not self._initialized:
            await self.initialize()
            if not self._initialized:
                return []

        logger.info(f"Searching memory: '{query}'")

        # Build filter
        where_filter = {}
        if doc_type:
            where_filter["doc_type"] = doc_type
        if meeting_id:
            where_filter["meeting_id"] = meeting_id

        try:
            # Get query embedding
            query_embedding = None
            if self._embedding_model:
                query_embedding = self._embedding_model.encode([query]).tolist()

            # Search
            if query_embedding:
                results = self._collection.query(
                    query_embeddings=query_embedding,
                    n_results=n_results,
                    where=where_filter if where_filter else None
                )
            else:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter if where_filter else None
                )

            # Parse results
            search_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    # Convert distance to similarity score (0-1)
                    score = 1 / (1 + distance)
                    
                    search_results.append(SearchResult(
                        document=MemoryDocument(
                            id=results['ids'][0][i],
                            meeting_id=metadata.get('meeting_id', 0),
                            content=doc,
                            doc_type=metadata.get('doc_type', 'unknown'),
                            metadata=metadata
                        ),
                        score=score,
                        snippet=doc[:200] + "..." if len(doc) > 200 else doc
                    ))

            logger.info(f"Found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def query_with_llm(
        self,
        question: str,
        llm_pipeline: Any,
        n_context: int = 5
    ) -> str:
        """Answer a question using RAG."""
        if not self._initialized or not llm_pipeline:
            return "Memory system not available."

        # Search for relevant context
        results = await self.search(question, n_results=n_context)
        
        if not results:
            return "No relevant information found in meeting history."

        # Build context
        context_parts = []
        for result in results:
            doc = result.document
            context_parts.append(
                f"[Meeting {doc.meeting_id}, {doc.doc_type}]: {doc.content}"
            )
        
        context = "\n\n".join(context_parts)

        # Generate answer
        prompt = f"""Based on the following meeting history, answer the question.

Meeting History:
{context}

Question: {question}

Answer based only on the information provided. If the information is not available, say so."""

        try:
            answer = await llm_pipeline._call_llm(prompt)
            return answer
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return "Failed to generate answer."

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            chunk_end = min(i + chunk_size, len(words))
            chunk = ' '.join(words[i:chunk_end])
            chunks.append(chunk)
            i += chunk_size - overlap
        
        return chunks

    async def get_meeting_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent meeting summaries from memory."""
        if not self._initialized:
            return []

        try:
            # Get all summaries
            results = self._collection.get(
                where={"doc_type": "summary"},
                limit=limit
            )
            
            meetings = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    meetings.append({
                        "meeting_id": metadata.get('meeting_id'),
                        "summary": doc,
                        "timestamp": metadata.get('timestamp'),
                        "platform": metadata.get('platform')
                    })
            
            return meetings
            
        except Exception as e:
            logger.error(f"Failed to get meeting history: {e}")
            return []

    async def delete_meeting(self, meeting_id: int) -> bool:
        """Delete all documents for a meeting."""
        if not self._initialized:
            return False

        try:
            self._collection.delete(
                where={"meeting_id": meeting_id}
            )
            logger.info(f"Deleted meeting {meeting_id} from memory")
            return True
        except Exception as e:
            logger.error(f"Failed to delete meeting: {e}")
            return False
