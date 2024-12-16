from typing import Tuple, Dict, Any, Optional
from dotenv import load_dotenv
import os
import json
from Components.logger import setup_logger
from Components.llm_providers import get_llm_provider, LLMProvider

# Setup logger
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize default LLM provider
DEFAULT_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
llm_provider: LLMProvider = get_llm_provider(DEFAULT_PROVIDER)

def extract_times(json_string: str) -> Tuple[int, int]:
    """
    Extract start and end times from JSON string.
    
    Args:
        json_string: JSON string containing start and end times
        
    Returns:
        Tuple[int, int]: Start and end times as integers
    """
    try:
        # Parse the JSON string
        data = json.loads(json_string)
        
        # Extract start and end times, removing 's' if present
        start_str = str(data[0]["start"]).replace('s', '')
        end_str = str(data[0]["end"]).replace('s', '')
        
        # Convert to floats
        start_time = float(start_str)
        end_time = float(end_str)
        
        # Convert to integers
        start_time_int = int(start_time)
        end_time_int = int(end_time)
        
        logger.debug(f"Extracted times: start={start_time_int}, end={end_time_int}")
        return start_time_int, end_time_int
    except Exception as e:
        logger.error(f"Error extracting times from JSON: {e}")
        return 0, 0

def GetHighlight(
    transcription: str,
    provider: Optional[str] = None,
    temperature: float = 0.7
) -> Tuple[int, int]:
    """
    Get highlight timestamps from transcription using specified LLM provider.
    
    Args:
        transcription: Text transcription with timestamps
        provider: Optional provider name ('openai', 'groq', or 'ollama')
        temperature: Temperature for text generation (default: 0.7)
        
    Returns:
        Tuple[int, int]: Start and end times for the highlight
    """
    global llm_provider
    
    try:
        # Update provider if specified
        if provider and provider != DEFAULT_PROVIDER:
            llm_provider = get_llm_provider(provider)
            logger.info(f"Switched to {provider} provider")
        
        logger.info(f"Getting highlight from transcription using {provider or DEFAULT_PROVIDER}")
        
        # Format transcription for better LLM understanding
        formatted_transcription = "Here's the video transcription with timestamps:\n\n"
        segments = []
        
        if isinstance(transcription, dict):
            # Handle dictionary format
            for segment in transcription.get('segments', []):
                start = int(segment.get('start', 0))
                text = segment.get('text', '').strip()
                segments.append((start, text))
        else:
            # Handle string format (parse existing format)
            for line in transcription.split('\n'):
                if ':' in line:
                    try:
                        time_str, text = line.split(':', 1)
                        start = int(float(time_str.strip().replace('s', '')))
                        segments.append((start, text.strip()))
                    except:
                        continue
                        
        # Reduzir o número de segmentos para evitar exceder o limite de tokens
        # Vamos pegar apenas segmentos a cada 5 segundos
        filtered_segments = []
        last_time = -5  # Iniciar com -5 para garantir que o primeiro segmento seja incluído
        
        for start, text in segments:
            if start - last_time >= 5:  # Só incluir se passou pelo menos 5 segundos
                filtered_segments.append((start, text))
                last_time = start
                
        # Limitar a 50 segmentos no total
        if len(filtered_segments) > 50:
            # Pegar 25 do início e 25 do fim para manter contexto
            filtered_segments = filtered_segments[:25] + filtered_segments[-25:]
            
        # Formatar o texto final
        for start, text in filtered_segments:
            formatted_transcription += f"{start}s: {text}\n"
            
        logger.debug(f"Formatted transcription:\n{formatted_transcription}")
        
        # Generate completion
        prompt = f"""You are a video editor assistant. Your task is to find the most engaging segment of a video based on its transcription.

Rules:
1. The segment should be between 15 and 60 seconds long
2. Choose a segment that is self-contained and makes sense on its own
3. The segment should capture the most interesting or engaging part of the video
4. IMPORTANT: Return ONLY a JSON object with start and end timestamps in seconds
5. The timestamps MUST be numbers from the transcription, do not make up new timestamps

Example response:
{{"start": 45, "end": 95}}

Here's the transcription:

{formatted_transcription}

Find the most engaging segment and return the start and end timestamps in JSON format:"""

        logger.debug(f"Sending prompt to LLM:\n{prompt}")
        
        try:
            if llm_provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature
                )
                completion = response.choices[0].message.content
            elif llm_provider == "groq":
                response = groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="mixtral-8x7b-32768",
                    temperature=temperature
                )
                completion = response.choices[0].message.content
                
                # Salvar resposta completa do Groq para análise
                with open('logs/groq_response.json', 'w', encoding='utf-8') as f:
                    json.dump({
                        'prompt': prompt,
                        'response': response.dict(),
                        'completion': completion
                    }, f, indent=2, ensure_ascii=False)
            else:  # ollama
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'mistral',
                        'prompt': prompt,
                        'temperature': temperature
                    }
                )
                completion = response.json()['response']
                
            logger.debug(f"LLM response:\n{completion}")
            
            # Parse JSON response
            try:
                result = json.loads(completion)
                start = int(result['start'])
                end = int(result['end'])
                
                # Validate timestamps
                if not isinstance(start, int) or not isinstance(end, int):
                    raise ValueError("Timestamps must be integers")
                    
                if end - start < 15 or end - start > 60:
                    raise ValueError("Segment must be between 15 and 60 seconds")
                    
                return start, end
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse LLM response: {str(e)}")
                logger.error(f"Raw response: {completion}")
                raise ValueError(f"Invalid response format: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error getting highlight: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error getting highlight: {e}")
        return 0, 0

if __name__ == "__main__":
    # Example usage with different providers
    USER_TEST: str = '''
    This is a test transcription with timestamps.
    0:00 - Introduction
    0:15 - Main topic discussion
    0:45 - Interesting highlight
    1:30 - Conclusion
    '''
    
    # Test with default provider
    result = GetHighlight(USER_TEST)
    logger.info(f"Default provider result: {result}")
    
    # Test with Groq
    result_groq = GetHighlight(USER_TEST, provider="groq")
    logger.info(f"Groq provider result: {result_groq}")
    
    # Test with Ollama
    result_ollama = GetHighlight(USER_TEST, provider="ollama")
    logger.info(f"Ollama provider result: {result_ollama}")
