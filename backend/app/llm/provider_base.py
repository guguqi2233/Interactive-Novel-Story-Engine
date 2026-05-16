from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

Message = dict[str, str]
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot complete a request."""


class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        """Generate plain text from chat-style messages."""

    @abstractmethod
    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        """Generate and validate structured JSON with a Pydantic schema."""

