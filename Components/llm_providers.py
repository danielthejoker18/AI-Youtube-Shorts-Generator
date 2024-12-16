from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
import os
from openai import OpenAI
from groq import Groq
import requests
import json
from time import sleep
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm
from Components.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    This class defines the interface for all LLM providers in the system.
    Each provider must implement the generate_completion method.
    
    Attributes:
        None
    """
    
    @abstractmethod
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate completion from the LLM provider.
        
        Args:
            system_prompt (str): The system context/instruction
            user_prompt (str): The user's input prompt
            temperature (float, optional): Sampling temperature. Defaults to 0.7
            
        Returns:
            str: The generated completion text
            
        Raises:
            NotImplementedError: If the child class doesn't implement this method
        """
        pass

@sleep_and_retry
@limits(calls=50, period=60)  # 50 calls per minute
class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider implementation.
    
    This class handles communication with OpenAI's API, including rate limiting
    and automatic retries on failure.
    
    Attributes:
        api_key (str): OpenAI API key
        client (OpenAI): OpenAI client instance
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, will look for OPENAI_API env var
            
        Raises:
            ValueError: If no API key is found
        """
        self.api_key = api_key or os.getenv('OPENAI_API')
        if not self.api_key:
            logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key not found")
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI provider initialized successfully")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate completion using OpenAI API with retry mechanism.
        
        Args:
            system_prompt (str): The system context/instruction
            user_prompt (str): The user's input prompt
            temperature (float, optional): Sampling temperature. Defaults to 0.7
            
        Returns:
            str: The generated completion text
            
        Raises:
            Exception: If API call fails after all retries
        """
        try:
            with tqdm(total=1, desc="Generating OpenAI completion") as pbar:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                pbar.update(1)
            
            logger.debug(f"OpenAI response received: {len(response.choices[0].message.content)} chars")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

@sleep_and_retry
@limits(calls=50, period=60)  # 50 calls per minute
class GroqProvider(LLMProvider):
    """
    Groq Cloud API provider implementation.
    
    This class handles communication with Groq's API, including rate limiting
    and automatic retries on failure.
    
    Attributes:
        api_key (str): Groq API key
        client (Groq): Groq client instance
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq client.
        
        Args:
            api_key (str, optional): Groq API key. If not provided, will look for GROQ_API_KEY env var
            
        Raises:
            ValueError: If no API key is found
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            logger.error("Groq API key not found")
            raise ValueError("Groq API key not found")
        self.client = Groq(api_key=self.api_key)
        logger.info("Groq provider initialized successfully")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate completion using Groq API with retry mechanism.
        
        Args:
            system_prompt (str): The system context/instruction
            user_prompt (str): The user's input prompt
            temperature (float, optional): Sampling temperature. Defaults to 0.7
            
        Returns:
            str: The generated completion text
            
        Raises:
            Exception: If API call fails after all retries
        """
        try:
            with tqdm(total=1, desc="Generating Groq completion") as pbar:
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Groq's most capable model
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                pbar.update(1)
            
            logger.debug(f"Groq response received: {len(response.choices[0].message.content)} chars")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise

class OllamaProvider(LLMProvider):
    """
    Local Ollama provider implementation.
    
    This class handles communication with a local Ollama instance.
    
    Attributes:
        host (str): Ollama host URL
        model (str): Ollama model name
    """
    
    def __init__(self, host: str = "http://localhost:11434"):
        """
        Initialize Ollama connection.
        
        Args:
            host (str, optional): Ollama host URL. Defaults to "http://localhost:11434"
            
        Raises:
            Exception: If connection to Ollama fails
        """
        self.host = host
        self.model = "mixtral"  # Default model
        # Test connection
        try:
            response = requests.get(f"{self.host}/api/version")
            response.raise_for_status()
            logger.info("Ollama provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate completion using local Ollama instance with retry mechanism.
        
        Args:
            system_prompt (str): The system context/instruction
            user_prompt (str): The user's input prompt
            temperature (float, optional): Sampling temperature. Defaults to 0.7
            
        Returns:
            str: The generated completion text
            
        Raises:
            Exception: If API call fails after all retries
        """
        try:
            with tqdm(total=1, desc="Generating Ollama completion") as pbar:
                response = requests.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "temperature": temperature,
                        "stream": False
                    }
                )
                response.raise_for_status()
                pbar.update(1)
            
            logger.debug(f"Ollama response received: {len(response.json()['response'])} chars")
            return response.json()["response"]
            
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise

def get_llm_provider(provider: str = "openai") -> LLMProvider:
    """
    Factory function to get LLM provider instance.
    
    Args:
        provider (str, optional): Provider name ('openai', 'groq', or 'ollama'). Defaults to "openai"
        
    Returns:
        LLMProvider: Instance of the specified provider
        
    Raises:
        ValueError: If unknown provider is specified
    """
    providers = {
        "openai": OpenAIProvider,
        "groq": GroqProvider,
        "ollama": OllamaProvider
    }
    
    if provider not in providers:
        logger.error(f"Unknown provider: {provider}. Available providers: {list(providers.keys())}")
        raise ValueError(f"Unknown provider: {provider}. Available providers: {list(providers.keys())}")
    
    try:
        return providers[provider]()
    except Exception as e:
        logger.error(f"Failed to initialize {provider} provider: {str(e)}")
        raise
