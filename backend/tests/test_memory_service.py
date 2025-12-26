"""
Unit tests for the Memory Service (Phase 3: Cognitive Persistence).

These tests verify the core functionality of storing and retrieving memories
with vector embeddings for semantic search.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch


class TestMemoryService:
    """Test cases for MemoryService class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        db.execute = Mock()
        return db
    
    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService instance."""
        from backend.app.core.memory import MemoryService
        return MemoryService()
    
    @pytest.mark.asyncio
    async def test_store_memory_creates_record(self, memory_service, mock_db):
        """Test that store_memory creates a memory record in the database."""
        # Mock the embedding generation
        with patch.object(memory_service, '_get_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1536  # Mock embedding vector
            
            memory = await memory_service.store_memory(
                user_id="test-user-123",
                content="User prefers morning meetings",
                memory_type="preference",
                db=mock_db,
                source="test"
            )
            
            # Verify DB operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_embed.assert_called_once_with("User prefers morning meetings")
    
    @pytest.mark.asyncio
    async def test_store_memory_handles_string_type(self, memory_service, mock_db):
        """Test that store_memory handles string memory types."""
        with patch.object(memory_service, '_get_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = None  # Simulate no embedding
            
            memory = await memory_service.store_memory(
                user_id="test-user",
                content="Test content",
                memory_type="decision",  # String type
                db=mock_db
            )
            
            mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_context_uses_keyword_fallback(self, memory_service, mock_db):
        """Test that retrieve_context falls back to keyword search without embeddings."""
        # Mock no embedding available
        with patch.object(memory_service, '_get_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = None
            
            # Mock DB query
            mock_memory = Mock()
            mock_memory.content = "User prefers morning meetings"
            mock_memory.access_count = 0
            mock_memory.last_accessed_at = None
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [mock_memory]
            mock_db.query.return_value = mock_query
            
            memories = await memory_service.retrieve_context(
                user_id="test-user",
                query="morning",
                db=mock_db,
                limit=5
            )
            
            # Should use keyword search
            assert mock_db.query.called
    
    @pytest.mark.asyncio
    async def test_get_embedding_handles_no_client(self, memory_service):
        """Test that _get_embedding returns None when OpenAI is not available."""
        # Ensure no OpenAI client
        memory_service._openai_client = None
        
        with patch.object(memory_service, 'openai_client', None):
            result = await memory_service._get_embedding("test text")
            assert result is None
    
    def test_format_context_for_prompt_empty(self, memory_service):
        """Test format_context_for_prompt with empty list."""
        result = memory_service.format_context_for_prompt([])
        assert result == ""
    
    def test_format_context_for_prompt_with_memories(self, memory_service):
        """Test format_context_for_prompt formats memories correctly."""
        from backend.app.models import MemoryType
        
        mock_memory = Mock()
        mock_memory.memory_type = MemoryType.PREFERENCE
        mock_memory.content = "User prefers morning meetings"
        mock_memory.created_at = datetime(2024, 1, 15)
        
        result = memory_service.format_context_for_prompt([mock_memory])
        
        assert "RELEVANT PAST CONTEXT" in result
        assert "User preference" in result
        assert "Jan 15" in result
        assert "morning meetings" in result


class TestMemoryModel:
    """Test cases for Memory SQLAlchemy model."""
    
    def test_memory_type_enum_values(self):
        """Test that MemoryType enum has expected values."""
        from backend.app.models import MemoryType
        
        assert MemoryType.DECISION.value == "decision"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.STANDUP_FOCUS.value == "standup_focus"
        assert MemoryType.TASK_COMPLETION.value == "task_completion"
    
    def test_memory_model_exists(self):
        """Test that Memory model is defined."""
        from backend.app.models import Memory
        
        assert Memory.__tablename__ == "memories"


# Run with: python -m pytest tests/test_memory_service.py -v
