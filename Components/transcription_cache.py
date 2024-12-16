import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from .logger import get_logger

logger = get_logger(__name__)

class TranscriptionCache:
    """Gerencia o cache de transcrições de vídeos"""
    
    def __init__(self, cache_dir: str = "cache/transcriptions"):
        """
        Inicializa o gerenciador de cache.
        
        Args:
            cache_dir: Diretório para armazenar os arquivos de cache
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Garante que o diretório de cache existe"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, video_id: str) -> Path:
        """Retorna o caminho do arquivo de cache para um vídeo"""
        return self.cache_dir / f"{video_id}.json"
        
    def get_transcription(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Tenta obter uma transcrição do cache.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dict com a transcrição ou None se não encontrada/inválida
        """
        cache_path = self._get_cache_path(video_id)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validar dados básicos
            required_fields = ['text', 'source', 'cached_at']
            if not all(field in data for field in required_fields):
                logger.warning(f"Invalid cache file for video {video_id}")
                return None
                
            logger.info(f"Found cached transcription for video {video_id}")
            logger.debug(f"Transcription cached at: {data['cached_at']}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading cache for video {video_id}: {e}")
            return None
            
    def save_transcription(self, video_id: str, transcription: Dict[str, Any]) -> bool:
        """
        Salva uma transcrição no cache.
        
        Args:
            video_id: ID do vídeo
            transcription: Dados da transcrição
            
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            # Adiciona metadados do cache
            cache_data = {
                **transcription,
                'cached_at': datetime.now().isoformat()
            }
            
            cache_path = self._get_cache_path(video_id)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved transcription to cache for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache for video {video_id}: {e}")
            return False
            
    def clear_cache(self, video_id: Optional[str] = None):
        """
        Limpa o cache de transcrições.
        
        Args:
            video_id: Se fornecido, limpa apenas o cache deste vídeo.
                     Se None, limpa todo o cache.
        """
        try:
            if video_id:
                cache_path = self._get_cache_path(video_id)
                if cache_path.exists():
                    cache_path.unlink()
                    logger.info(f"Cleared cache for video {video_id}")
            else:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                logger.info("Cleared all transcription cache")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            
    def get_cache_size(self) -> int:
        """Retorna o número de transcrições em cache"""
        return len(list(self.cache_dir.glob("*.json")))
        
    def get_cache_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cache"""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_files': len(cache_files),
                'total_size_bytes': total_size,
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'cache_dir': str(self.cache_dir),
                'error': str(e)
            }
