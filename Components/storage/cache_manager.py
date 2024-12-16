"""
Gerenciamento de cache do sistema.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import CacheError

logger = ComponentLogger(__name__)

class CacheManager:
    """
    Gerencia o cache do sistema.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de cache.
        
        Args:
            cache_dir: Diretório para armazenar cache
        """
        self.cache_dir = cache_dir or config.paths.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de metadados do cache
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """
        Carrega metadados do cache.
        
        Returns:
            Dict com metadados
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar metadados do cache: {e}")
        return {}
    
    def _save_metadata(self):
        """Salva metadados do cache."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar metadados do cache: {e}")
    
    def _get_cache_key(self, data: Any) -> str:
        """
        Gera chave única para os dados.
        
        Args:
            data: Dados para gerar chave
            
        Returns:
            String hash MD5
        """
        if isinstance(data, (str, bytes)):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        if isinstance(content, str):
            content = content.encode()
            
        return hashlib.md5(content).hexdigest()
    
    def get(self, key: str, max_age: Optional[timedelta] = None) -> Optional[Any]:
        """
        Recupera dados do cache.
        
        Args:
            key: Chave dos dados
            max_age: Idade máxima dos dados
            
        Returns:
            Dados ou None se não encontrado/expirado
        """
        try:
            cache_file = self.cache_dir / f"{key}.json"
            if not cache_file.exists():
                return None
            
            # Verifica idade se especificada
            if max_age is not None:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - mtime > max_age:
                    self.remove(key)
                    return None
            
            with open(cache_file, "r") as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"Erro ao ler cache '{key}': {e}")
            return None
    
    def set(self, key: str, data: Any, metadata: Optional[Dict] = None):
        """
        Armazena dados no cache.
        
        Args:
            key: Chave dos dados
            data: Dados para armazenar
            metadata: Metadados opcionais
        """
        try:
            # Salva dados
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            
            # Atualiza metadados
            if metadata:
                self.metadata[key] = {
                    "created": datetime.now().isoformat(),
                    **metadata
                }
                self._save_metadata()
                
        except Exception as e:
            raise CacheError(f"Erro ao salvar cache '{key}': {e}")
    
    def remove(self, key: str):
        """
        Remove dados do cache.
        
        Args:
            key: Chave dos dados
        """
        try:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
            
            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()
                
        except Exception as e:
            logger.warning(f"Erro ao remover cache '{key}': {e}")
    
    def clear(self, older_than: Optional[timedelta] = None):
        """
        Limpa todo o cache ou apenas entradas antigas.
        
        Args:
            older_than: Se especificado, remove apenas entradas mais antigas
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.name == "cache_metadata.json":
                    continue
                    
                if older_than is not None:
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if datetime.now() - mtime <= older_than:
                        continue
                
                cache_file.unlink()
            
            if older_than is None:
                self.metadata = {}
                self._save_metadata()
                
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
    
    def get_size(self) -> int:
        """
        Retorna tamanho total do cache em bytes.
        
        Returns:
            Tamanho em bytes
        """
        try:
            return sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho do cache: {e}")
            return 0
