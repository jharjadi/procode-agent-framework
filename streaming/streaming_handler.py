"""
Streaming handler for real-time response delivery.
Provides utilities for streaming text and progress updates.
"""

import asyncio
from typing import AsyncGenerator, List
from a2a.types import Part, TextPart


class StreamingHandler:
    """Handler for streaming responses token-by-token or chunk-by-chunk."""
    
    def __init__(self, chunk_size: int = 5, delay: float = 0.01):
        """
        Initialize the streaming handler.
        
        Args:
            chunk_size: Number of words per chunk
            delay: Delay between chunks in seconds (simulates streaming)
        """
        self.chunk_size = chunk_size
        self.delay = delay
    
    async def stream_text(self, text: str) -> AsyncGenerator[Part, None]:
        """
        Stream text as Parts, chunk by chunk.
        
        Args:
            text: Text to stream
            
        Yields:
            TextPart objects containing chunks of text
        """
        chunks = self._chunk_text(text)
        for chunk in chunks:
            yield TextPart(text=chunk)
            await asyncio.sleep(self.delay)
    
    async def stream_progress(self, messages: List[str]) -> AsyncGenerator[Part, None]:
        """
        Stream progress messages.
        
        Args:
            messages: List of progress messages to stream
            
        Yields:
            TextPart objects containing progress messages
        """
        for message in messages:
            yield TextPart(text=message + "\n")
            await asyncio.sleep(self.delay * 5)  # Longer delay for progress messages
    
    async def stream_with_progress(
        self, 
        progress_messages: List[str], 
        final_text: str
    ) -> AsyncGenerator[Part, None]:
        """
        Stream progress messages followed by final text.
        
        Args:
            progress_messages: List of progress messages
            final_text: Final response text
            
        Yields:
            TextPart objects for progress and final response
        """
        # Stream progress messages
        async for part in self.stream_progress(progress_messages):
            yield part
        
        # Stream final text
        async for part in self.stream_text(final_text):
            yield part
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for streaming.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk_words = words[i:i + self.chunk_size]
            chunk = " ".join(chunk_words)
            
            # Add space after chunk unless it's the last one
            if i + self.chunk_size < len(words):
                chunk += " "
            
            chunks.append(chunk)
        
        return chunks


class ProgressTracker:
    """Track and stream progress updates for long-running operations."""
    
    def __init__(self):
        self.steps: List[str] = []
        self.current_step: int = 0
    
    def add_step(self, description: str):
        """Add a step to track."""
        self.steps.append(description)
    
    async def stream_step(self, step_index: int) -> AsyncGenerator[Part, None]:
        """
        Stream a progress step.
        
        Args:
            step_index: Index of the step to stream
            
        Yields:
            TextPart with progress message
        """
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            message = f"[{step_index + 1}/{len(self.steps)}] {self.steps[step_index]}"
            yield TextPart(text=message + "\n")
            await asyncio.sleep(0.05)
    
    async def stream_all_steps(self) -> AsyncGenerator[Part, None]:
        """
        Stream all progress steps sequentially.
        
        Yields:
            TextPart objects for each step
        """
        for i in range(len(self.steps)):
            async for part in self.stream_step(i):
                yield part
