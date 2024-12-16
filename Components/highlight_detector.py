from typing import List, Dict, Any, Optional
import os
from groq import Groq
from .logger import get_logger

logger = get_logger(__name__)

class HighlightDetector:
    """Detecta os melhores momentos em uma transcrição usando LLM"""
    
    def __init__(self):
        """Inicializa o detector de highlights"""
        self.client = Groq(
            api_key=os.getenv('GROQ_API_KEY')
        )
        
    def _chunk_segments(self, segments: List[Dict[str, Any]], max_segments: int = 30) -> List[List[Dict[str, Any]]]:
        """
        Divide os segmentos em chunks menores para evitar limite de tokens
        
        Args:
            segments: Lista de segmentos
            max_segments: Número máximo de segmentos por chunk
            
        Returns:
            Lista de chunks de segmentos
        """
        chunks = []
        for i in range(0, len(segments), max_segments):
            chunk = segments[i:i + max_segments]
            chunks.append(chunk)
        return chunks
        
    def _detect_highlights_chunk(self, segments: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Detecta highlights em um chunk de segmentos
        
        Args:
            segments: Lista de segmentos do chunk
            
        Returns:
            Lista de highlights ou None se falhar
        """
        try:
            # Format segments for prompt
            segments_text = "\n".join([
                f"[{s['start']:.1f}s - {s['end']:.1f}s] {s['text']}"
                for s in segments
            ])
            
            logger.info(f"Processing {len(segments)} segments in chunk")
            logger.debug(f"Segments text: {segments_text[:500]}...")
            
            # Prompt para o LLM
            prompt = f"""
            Analise a transcrição abaixo e identifique os melhores momentos para criar shorts virais.
            
            REGRAS CRÍTICAS:
            1. MÍNIMO de 5 segundos por momento
            2. MÁXIMO de 60 segundos por momento
            3. Combine segmentos consecutivos quando necessário
            4. Certifique-se que o texto faça sentido completo
            
            CRITÉRIOS DE SELEÇÃO:
            1. Priorize momentos com alto potencial viral:
               - Frases impactantes ou polêmicas
               - Revelações surpreendentes
               - Momentos emocionantes ou engraçados
               - Informações exclusivas ou novidades
               
            2. Garanta que cada momento:
               - Tenha início e fim claros
               - Possa ser entendido sem contexto adicional
               - Mantenha o interesse do espectador
               - Tenha um "gancho" para compartilhamento
            
            Transcrição com timestamps:
            {segments_text}
            
            IMPORTANTE: Retorne APENAS o JSON puro, sem markdown, sem explicações:
            {{
                "highlights": [
                    {{"start": timestamp_inicio, "end": timestamp_fim, "text": "texto do trecho"}},
                    {{"start": timestamp_inicio, "end": timestamp_fim, "text": "texto do trecho"}},
                    {{"start": timestamp_inicio, "end": timestamp_fim, "text": "texto do trecho"}}
                ]
            }}
            """
            
            # Faz a chamada para a API
            logger.info("Calling Groq API")
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em identificar os melhores momentos em vídeos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Log the response
            logger.debug(f"LLM response: {response.choices[0].message.content}")
            
            # Processa a resposta
            import json
            try:
                # Tenta fazer o parse do JSON da resposta
                response_text = response.choices[0].message.content.strip()
                if "```" in response_text:
                    # Remove blocos de código markdown se presentes
                    response_text = response_text.split("```")[1].strip()
                    if response_text.startswith("json"):
                        response_text = response_text[4:].strip()
                
                highlights_data = json.loads(response_text)
                
                # Valida e filtra os highlights
                valid_highlights = []
                for highlight in highlights_data.get("highlights", []):
                    start = float(highlight.get("start", 0))
                    end = float(highlight.get("end", 0))
                    text = highlight.get("text", "").strip()
                    
                    duration = end - start
                    if duration < 5:
                        # Se o highlight for muito curto, tenta estender até o próximo segmento
                        for segment in segments:
                            if float(segment["start"]) > end:
                                new_end = float(segment["end"])
                                if new_end - start >= 5:
                                    end = new_end
                                    text += " " + segment["text"]
                                    break
                    
                    duration = end - start
                    if 5 <= duration <= 60 and text:
                        valid_highlights.append({
                            "start": start,
                            "end": end,
                            "text": text
                        })
                    else:
                        logger.warning(f"Invalid duration: {duration}s for highlight {highlight}")
                
                if valid_highlights:
                    logger.info(f"Found {len(valid_highlights)} valid highlights")
                    return valid_highlights
                else:
                    logger.warning("No valid highlights found in chunk")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response.choices[0].message.content}")
                return None
                
        except Exception as e:
            logger.error(f"Error detecting highlights in chunk: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
    def detect_highlights(self, text: str, segments: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Detecta os melhores momentos em uma transcrição.
        
        Args:
            text: Texto completo da transcrição
            segments: Lista de segmentos com timestamps
            
        Returns:
            Lista de dicionários com informações dos highlights:
            [{'start': float, 'end': float, 'text': str}]
            ou None se falhar
        """
        try:
            if not segments:
                logger.error("No segments provided")
                return None
                
            # Divide em chunks menores
            chunks = self._chunk_segments(segments)
            logger.info(f"Processing {len(chunks)} chunks of segments")
            
            # Processa cada chunk
            all_highlights = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                highlights = self._detect_highlights_chunk(chunk)
                if highlights:
                    all_highlights.extend(highlights)
                    
            if all_highlights:
                # Ordena por duração (maior primeiro)
                all_highlights.sort(key=lambda x: x['end'] - x['start'], reverse=True)
                # Pega os 3 melhores
                best_highlights = all_highlights[:3]
                # Ordena por timestamp
                best_highlights.sort(key=lambda x: x['start'])
                
                logger.info(f"Found {len(best_highlights)} best highlights")
                return best_highlights
            else:
                logger.warning("No valid highlights found in any chunk")
                return None
                
        except Exception as e:
            logger.error(f"Error detecting highlights: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
