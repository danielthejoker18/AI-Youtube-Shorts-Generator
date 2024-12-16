"""
Implementação do provedor Ollama.
"""

import os
from typing import List, Optional
import requests

from .llm_provider import (
    LLMProvider,
    ProviderType,
    Message,
    CompletionResult
)
from ..core.exceptions import APIError

class OllamaProvider(LLMProvider):
    """
    Provedor Ollama.
    """
    
    # Modelos disponíveis
    LLAMA2 = "llama2"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"
    
    # Tamanhos de contexto
    CONTEXT_SIZES = {
        LLAMA2: 4096,
        MISTRAL: 8192,
        CODELLAMA: 16384
    }
    
    def __init__(self, host: str = "http://localhost:11434"):
        """
        Inicializa provedor.
        
        Args:
            host: Host do Ollama
        """
        super().__init__()
        self.host = host.rstrip("/")
        
        # Valida conexão
        if not self.validate_api_key():
            raise ValueError(f"Não foi possível conectar ao Ollama em {host}")
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA
    
    @property
    def available_models(self) -> List[str]:
        return [
            self.LLAMA2,
            self.MISTRAL,
            self.CODELLAMA
        ]
    
    def validate_api_key(self) -> bool:
        try:
            # Tenta listar modelos
            response = requests.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def get_model_context_size(self, model: str) -> int:
        if model not in self.CONTEXT_SIZES:
            raise APIError(f"Modelo inválido: {model}")
        return self.CONTEXT_SIZES[model]
    
    def count_tokens(self, text: str, model: str) -> int:
        # Ollama não tem contagem precisa, usa estimativa
        return len(text.split()) * 1.3
    
    def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> CompletionResult:
        # Usa Mistral por padrão
        model = model or self.MISTRAL
        
        # Valida parâmetros
        self.validate_completion_params(model, temperature, max_tokens)
        
        try:
            # Converte mensagens para prompt
            prompt = self.format_chat_prompt(messages)
            
            # Prepara request
            data = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            }
            
            if max_tokens:
                data["max_tokens"] = max_tokens
                
            if stop:
                data["stop"] = stop
            
            # Faz request
            response = requests.post(
                f"{self.host}/api/generate",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            # Processa resposta
            return CompletionResult(
                text=result["response"],
                tokens_used=int(self.count_tokens(prompt + result["response"], model)),
                finish_reason="stop",
                model=model,
                provider=self.provider_type
            )
            
        except Exception as e:
            raise APIError(f"Erro na API Ollama: {e}")
    
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
