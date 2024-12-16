"""
Interface base para provedores LLM.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..core.logger import ComponentLogger
from ..core.exceptions import APIError

logger = ComponentLogger(__name__)

class ProviderType(Enum):
    """Tipos de provedores suportados."""
    
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"

@dataclass
class Message:
    """Mensagem para o LLM."""
    
    role: str
    content: str

@dataclass
class CompletionResult:
    """Resultado de uma completion."""
    
    text: str
    tokens_used: int
    finish_reason: str
    model: str
    provider: ProviderType

class LLMProvider(ABC):
    """
    Interface base para provedores LLM.
    """
    
    def __init__(self):
        """Inicializa o provedor."""
        self.logger = logger
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Tipo do provedor."""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Lista de modelos disponíveis."""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        Valida chave de API.
        
        Returns:
            True se válida
        """
        pass
    
    @abstractmethod
    def get_model_context_size(self, model: str) -> int:
        """
        Retorna tamanho do contexto de um modelo.
        
        Args:
            model: Nome do modelo
            
        Returns:
            Tamanho do contexto em tokens
            
        Raises:
            APIError: Se modelo inválido
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Conta tokens em um texto.
        
        Args:
            text: Texto para contar
            model: Modelo para usar
            
        Returns:
            Número de tokens
            
        Raises:
            APIError: Se erro na contagem
        """
        pass
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> CompletionResult:
        """
        Gera completion para uma conversa.
        
        Args:
            messages: Lista de mensagens
            model: Modelo para usar
            temperature: Temperatura (0-1)
            max_tokens: Limite de tokens
            stop: Sequências para parar
            
        Returns:
            Resultado da completion
            
        Raises:
            APIError: Se erro na API
        """
        pass
    
    @abstractmethod
    def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> CompletionResult:
        """
        Gera completion para um prompt.
        
        Args:
            prompt: Texto do prompt
            model: Modelo para usar
            temperature: Temperatura (0-1)
            max_tokens: Limite de tokens
            stop: Sequências para parar
            
        Returns:
            Resultado da completion
            
        Raises:
            APIError: Se erro na API
        """
        pass
    
    def validate_completion_params(
        self,
        model: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ):
        """
        Valida parâmetros de completion.
        
        Args:
            model: Modelo para usar
            temperature: Temperatura
            max_tokens: Limite de tokens
            
        Raises:
            ValueError: Se parâmetros inválidos
        """
        # Valida modelo
        if model and model not in self.available_models:
            raise ValueError(f"Modelo inválido: {model}")
        
        # Valida temperatura
        if not 0 <= temperature <= 1:
            raise ValueError(f"Temperatura inválida: {temperature}")
        
        # Valida tokens
        if max_tokens is not None:
            if max_tokens <= 0:
                raise ValueError(f"max_tokens inválido: {max_tokens}")
            
            if model:
                context_size = self.get_model_context_size(model)
                if max_tokens > context_size:
                    raise ValueError(
                        f"max_tokens ({max_tokens}) maior que contexto "
                        f"do modelo ({context_size})"
                    )
    
    def format_chat_prompt(self, messages: List[Message]) -> str:
        """
        Formata mensagens como prompt de texto.
        
        Args:
            messages: Lista de mensagens
            
        Returns:
            Prompt formatado
        """
        formatted = []
        for msg in messages:
            if msg.role == "system":
                formatted.append(f"System: {msg.content}")
            elif msg.role == "user":
                formatted.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Assistant: {msg.content}")
            else:
                formatted.append(f"{msg.role}: {msg.content}")
        return "\n".join(formatted)
    
    def create_chat_completion(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> CompletionResult:
        """
        Helper para criar chat completion.
        
        Args:
            system: Prompt do sistema
            user: Prompt do usuário
            model: Modelo para usar
            temperature: Temperatura
            max_tokens: Limite de tokens
            stop: Sequências para parar
            
        Returns:
            Resultado da completion
        """
        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user)
        ]
        return self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop
        )
