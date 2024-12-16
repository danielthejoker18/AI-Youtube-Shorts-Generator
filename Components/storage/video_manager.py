"""
Gerenciamento de vídeos do sistema.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import ValidationError
from ..media.media_utils import VideoMetadata, get_video_metadata

logger = ComponentLogger(__name__)

@dataclass
class VideoInfo:
    """Informações sobre um vídeo."""
    
    video_id: str
    title: str
    path: Path
    metadata: VideoMetadata
    download_date: datetime
    processed: bool = False
    processing_date: Optional[datetime] = None
    error: Optional[str] = None

class VideoManager:
    """
    Gerencia o estado dos vídeos no sistema.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de vídeos."""
        self.videos_dir = config.paths.VIDEOS_DIR
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de estado
        self.state_file = self.videos_dir / "video_state.json"
        self.videos: Dict[str, VideoInfo] = self._load_state()
    
    def _load_state(self) -> Dict[str, VideoInfo]:
        """
        Carrega estado dos vídeos.
        
        Returns:
            Dict com informações dos vídeos
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    return {
                        vid: VideoInfo(
                            video_id=info["video_id"],
                            title=info["title"],
                            path=Path(info["path"]),
                            metadata=VideoMetadata(**info["metadata"]),
                            download_date=datetime.fromisoformat(info["download_date"]),
                            processed=info["processed"],
                            processing_date=datetime.fromisoformat(info["processing_date"])
                                if info.get("processing_date") else None,
                            error=info.get("error")
                        )
                        for vid, info in data.items()
                    }
            except Exception as e:
                logger.error(f"Erro ao carregar estado dos vídeos: {e}")
        return {}
    
    def _save_state(self):
        """Salva estado dos vídeos."""
        try:
            # Converte para dict serializável
            data = {
                vid: {
                    **asdict(info),
                    "path": str(info.path),
                    "download_date": info.download_date.isoformat(),
                    "processing_date": info.processing_date.isoformat()
                        if info.processing_date else None
                }
                for vid, info in self.videos.items()
            }
            
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar estado dos vídeos: {e}")
    
    def add_video(
        self,
        video_id: str,
        title: str,
        path: Path,
        validate: bool = True
    ) -> VideoInfo:
        """
        Adiciona um novo vídeo ao sistema.
        
        Args:
            video_id: ID do vídeo
            title: Título do vídeo
            path: Caminho do arquivo
            validate: Se True, valida o arquivo
            
        Returns:
            Informações do vídeo
            
        Raises:
            ValidationError: Se o vídeo não passar na validação
        """
        if video_id in self.videos:
            raise ValidationError(f"Vídeo '{video_id}' já existe")
            
        if not path.exists():
            raise ValidationError(f"Arquivo não encontrado: {path}")
            
        if validate:
            try:
                metadata = get_video_metadata(path)
            except Exception as e:
                raise ValidationError(f"Erro ao validar vídeo: {e}")
        
        video_info = VideoInfo(
            video_id=video_id,
            title=title,
            path=path,
            metadata=metadata,
            download_date=datetime.now()
        )
        
        self.videos[video_id] = video_info
        self._save_state()
        
        return video_info
    
    def get_video(self, video_id: str) -> Optional[VideoInfo]:
        """
        Recupera informações de um vídeo.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Informações do vídeo ou None se não encontrado
        """
        return self.videos.get(video_id)
    
    def mark_as_processed(self, video_id: str, error: Optional[str] = None):
        """
        Marca um vídeo como processado.
        
        Args:
            video_id: ID do vídeo
            error: Mensagem de erro se houver
        """
        if video_id not in self.videos:
            logger.warning(f"Vídeo não encontrado: {video_id}")
            return
            
        video = self.videos[video_id]
        video.processed = True
        video.processing_date = datetime.now()
        video.error = error
        
        self._save_state()
    
    def get_unprocessed_videos(self) -> List[VideoInfo]:
        """
        Retorna lista de vídeos não processados.
        
        Returns:
            Lista de informações dos vídeos
        """
        return [
            video for video in self.videos.values()
            if not video.processed
        ]
    
    def get_failed_videos(self) -> List[VideoInfo]:
        """
        Retorna lista de vídeos com erro.
        
        Returns:
            Lista de informações dos vídeos
        """
        return [
            video for video in self.videos.values()
            if video.processed and video.error is not None
        ]
    
    def remove_video(self, video_id: str, delete_file: bool = False):
        """
        Remove um vídeo do sistema.
        
        Args:
            video_id: ID do vídeo
            delete_file: Se True, exclui o arquivo
        """
        if video_id not in self.videos:
            logger.warning(f"Vídeo não encontrado: {video_id}")
            return
            
        video = self.videos[video_id]
        
        if delete_file and video.path.exists():
            try:
                video.path.unlink()
            except Exception as e:
                logger.error(f"Erro ao excluir arquivo: {e}")
        
        del self.videos[video_id]
        self._save_state()
    
    def cleanup(self, delete_files: bool = False):
        """
        Remove vídeos processados ou com erro.
        
        Args:
            delete_files: Se True, exclui os arquivos
        """
        for video in list(self.videos.values()):
            if video.processed:
                self.remove_video(video.video_id, delete_files)
