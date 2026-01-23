from typing import List

class ContentEmbedder:
    """
    Wrapper for OpenAI's text-embedding-3-small.
    Currently mocked to avoid API costs during dev.
    """
    
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.dimension = 1536

    def embed(self, text: str) -> List[float]:
        # Mock embedding vector of correct dimension
        # In real impl, this calls openai.embeddings.create
        return [0.1] * self.dimension
