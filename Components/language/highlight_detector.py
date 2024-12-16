"""
Detector de highlights em transcrições.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.logger import ComponentLogger
from ..core.exceptions import APIError
from ..providers.factory import create_provider
from ..providers.llm_provider import Message

logger = ComponentLogger(__name__)

@dataclass
class Highlight:
    """Highlight detectado."""
    
    start_time: float
    end_time: float
    text: str
    score: float
    reason: str

class HighlightDetector:
    """
    Detector de highlights usando LLM.
    """
    
    def __init__(
        self,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Inicializa detector.
        
        Args:
            provider_type: Tipo do provider LLM
            api_key: Chave de API opcional
        """
        self.logger = logger
        self.provider = create_provider(provider_type, api_key)
        
    def detect_highlights(
        self,
        transcript: List[Dict[str, Any]],
        min_duration: float = 10.0,
        max_duration: float = 60.0,
        min_score: float = 0.7,
        max_highlights: int = 5,
        language: str = "pt"
    ) -> List[Highlight]:
        """
        Detecta highlights em uma transcrição.
        
        Args:
            transcript: Lista de segmentos de transcrição
            min_duration: Duração mínima em segundos
            max_duration: Duração máxima em segundos
            min_score: Score mínimo (0-1)
            max_highlights: Número máximo de highlights
            language: Idioma do conteúdo
            
        Returns:
            Lista de highlights detectados
            
        Raises:
            APIError: Se erro no LLM
        """
        # Valida parâmetros
        if not transcript:
            return []
            
        if min_duration >= max_duration:
            raise ValueError("min_duration deve ser menor que max_duration")
            
        if not 0 <= min_score <= 1:
            raise ValueError("min_score deve estar entre 0 e 1")
            
        if max_highlights < 1:
            raise ValueError("max_highlights deve ser maior que 0")
        
        try:
            # Prepara prompt
            system = self._get_system_prompt(language)
            user = self._format_transcript(transcript)
            
            # Faz request
            result = self.provider.create_chat_completion(
                system=system,
                user=user,
                temperature=0.7
            )
            
            # Processa resposta
            return self._parse_highlights(
                result.text,
                transcript,
                min_duration,
                max_duration,
                min_score,
                max_highlights
            )
            
        except Exception as e:
            raise APIError(f"Erro detectando highlights: {e}")
    
    def _get_system_prompt(self, language: str) -> str:
        """
        Retorna prompt do sistema.
        
        Args:
            language: Idioma do conteúdo
            
        Returns:
            Prompt formatado
        """
        if language == "pt":
            return """Você é um especialista em análise de conteúdo de vídeo.
            
Sua tarefa é identificar os momentos mais interessantes e envolventes em uma transcrição de vídeo.

Para cada segmento potencial, avalie:
1. Engajamento: O quanto o conteúdo é cativante e interessante
2. Contexto: Se o segmento faz sentido isoladamente
3. Duração: Se o segmento tem uma duração adequada para shorts

Retorne os highlights no seguinte formato JSON:
{
    "highlights": [
        {
            "start_time": float,
            "end_time": float,
            "text": string,
            "score": float,
            "reason": string
        }
    ]
}

Onde:
- start_time/end_time: Tempo em segundos
- text: Texto do segmento
- score: Score de 0 a 1
- reason: Motivo da seleção

Retorne APENAS o JSON, sem texto adicional."""
        else:
            return """You are a video content analysis expert.
            
Your task is to identify the most interesting and engaging moments in a video transcript.

For each potential segment, evaluate:
1. Engagement: How captivating and interesting the content is
2. Context: If the segment makes sense in isolation
3. Duration: If the segment has an adequate duration for shorts

Return the highlights in the following JSON format:
{
    "highlights": [
        {
            "start_time": float,
            "end_time": float,
            "text": string,
            "score": float,
            "reason": string
        }
    ]
}

Where:
- start_time/end_time: Time in seconds
- text: Segment text
- score: Score from 0 to 1
- reason: Selection reason

Return ONLY the JSON, no additional text."""
    
    def _format_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """
        Formata transcrição para prompt.
        
        Args:
            transcript: Lista de segmentos
            
        Returns:
            Prompt formatado
        """
        segments = []
        for segment in transcript:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            segments.append(f"[{start:.1f} - {end:.1f}] {text}")
        return "\n".join(segments)
    
    def _parse_highlights(
        self,
        response: str,
        transcript: List[Dict[str, Any]],
        min_duration: float,
        max_duration: float,
        min_score: float,
        max_highlights: int
    ) -> List[Highlight]:
        """
        Processa resposta do LLM.
        
        Args:
            response: Resposta do LLM
            transcript: Transcrição original
            min_duration: Duração mínima
            max_duration: Duração máxima
            min_score: Score mínimo
            max_highlights: Máximo de highlights
            
        Returns:
            Lista de highlights
        """
        try:
            # Parse JSON
            data = json.loads(response)
            highlights = []
            
            # Processa cada highlight
            for h in data["highlights"]:
                # Valida duração
                duration = h["end_time"] - h["start_time"]
                if duration < min_duration or duration > max_duration:
                    continue
                    
                # Valida score
                if h["score"] < min_score:
                    continue
                
                # Adiciona highlight
                highlights.append(Highlight(
                    start_time=h["start_time"],
                    end_time=h["end_time"],
                    text=h["text"],
                    score=h["score"],
                    reason=h["reason"]
                ))
            
            # Ordena por score e limita
            highlights.sort(key=lambda x: x.score, reverse=True)
            return highlights[:max_highlights]
            
        except Exception as e:
            self.logger.error(f"Erro parseando highlights: {e}")
            return []
