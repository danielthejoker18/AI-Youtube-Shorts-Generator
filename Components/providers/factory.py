"""
Factory para criar providers LLM.
"""

import os
from typing import Optional

from .llm_provider import LLMProvider, ProviderType
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider
from .ollama_provider import OllamaProvider

def create_provider(
    provider_type: Optional[str] = None,
    api_key: Optional[str] = None
) -> LLMProvider:
    """
    Cria provider LLM.
    
    Args:
        provider_type: Tipo do provider (openai, groq, ollama)
        api_key: Chave de API opcional
        
    Returns:
        Provider LLM
        
    Raises:
        ValueError: Se provider inválido
    """
    # Usa provider do ambiente se não especificado
    provider_type = provider_type or os.getenv("LLM_PROVIDER", "openai")
    
    # Converte para enum
    try:
        provider_enum = ProviderType(provider_type.lower())
    except ValueError:
        raise ValueError(f"Provider inválido: {provider_type}")
    
    # Cria provider
    if provider_enum == ProviderType.OPENAI:
        return OpenAIProvider(api_key=api_key)
    elif provider_enum == ProviderType.GROQ:
        return GroqProvider(api_key=api_key)
    elif provider_enum == ProviderType.OLLAMA:
        return OllamaProvider()
    else:
        raise ValueError(f"Provider não implementado: {provider_type}")
