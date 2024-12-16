"""
Implementação do provedor OpenAI.
"""

import os
from typing import List, Optional, Dict

import openai
from openai import OpenAI

from .llm_provider import (
    LLMProvider,
    ProviderType,
    Message,
    CompletionResult
)
from ..core.exceptions import APIError

class OpenAIProvider(LLMProvider):
    """
    Provedor OpenAI.
    """
    
    # Modelos disponíveis
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-1106-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Tamanhos de contexto
    CONTEXT_SIZES = {
        GPT4: 8192,
        GPT4_TURBO: 128000,
        GPT35_TURBO: 4096
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa provedor.
        
        Args:
            api_key: Chave de API opcional
        """
        super().__init__()
        
        # Usa chave do ambiente se não fornecida
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key não encontrada")
            
        # Inicializa cliente
        self.client = OpenAI(api_key=self.api_key)
        
        # Valida chave
        if not self.validate_api_key():
            raise ValueError("OpenAI API key inválida")
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def available_models(self) -> List[str]:
        return [
            self.GPT4,
            self.GPT4_TURBO,
            self.GPT35_TURBO
        ]
    
    def validate_api_key(self) -> bool:
        try:
            # Tenta listar modelos
            self.client.models.list()
            return True
        except:
            return False
    
    def get_model_context_size(self, model: str) -> int:
        if model not in self.CONTEXT_SIZES:
            raise APIError(f"Modelo inválido: {model}")
        return self.CONTEXT_SIZES[model]
    
    def count_tokens(self, text: str, model: str) -> int:
        try:
            # Usa tiktoken para contar
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            raise APIError(f"Erro contando tokens: {e}")
    
    def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> CompletionResult:
        # Usa GPT-3.5 Turbo por padrão
        model = model or self.GPT35_TURBO
        
        # Valida parâmetros
        self.validate_completion_params(model, temperature, max_tokens)
        
        try:
            # Converte mensagens
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Faz request
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop
            )
            
            # Processa resposta
            choice = response.choices[0]
            return CompletionResult(
                text=choice.message.content,
                tokens_used=response.usage.total_tokens,
                finish_reason=choice.finish_reason,
                model=model,
                provider=self.provider_type
            )
            
        except Exception as e:
            raise APIError(f"Erro na API OpenAI: {e}")
    
    def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> CompletionResult:
        # Converte para chat completion
        messages = [Message(role="user", content=prompt)]
        return self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop
        )
