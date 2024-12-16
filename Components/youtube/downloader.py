"""
Download de vídeos do YouTube.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json

import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import DownloadError
from ..storage.video_manager import VideoManager

logger = ComponentLogger(__name__)

@dataclass
class VideoQuality:
    """Configuração de qualidade do vídeo."""
    
    height: int
    fps: Optional[int] = None
    ext: str = "mp4"
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    
    def to_format(self) -> str:
        """
        Converte para string de formato yt-dlp.
        
        Returns:
            String de formato
        """
        parts = []
        
        # Formato básico
        parts.append(f"bestvideo[height<={self.height}]")
        
        # Codec de vídeo
        if self.vcodec:
            parts[-1] += f"[vcodec={self.vcodec}]"
            
        # FPS
        if self.fps:
            parts[-1] += f"[fps<={self.fps}]"
            
        # Extensão
        parts[-1] += f"[ext={self.ext}]"
        
        # Áudio
        parts.append(f"bestaudio[ext={self.ext}]")
        if self.acodec:
            parts[-1] += f"[acodec={self.acodec}]"
            
        return f"{'+'.join(parts)}/best[height<={self.height}]"

class YouTubeDownloader:
    """
    Gerencia download de vídeos do YouTube.
    """
    
    # Qualidades predefinidas
    QUALITIES = {
        "1080p": VideoQuality(
            height=1080,
            fps=30,
            vcodec="h264",
            acodec="aac"
        ),
        "720p": VideoQuality(
            height=720,
            fps=30,
            vcodec="h264",
            acodec="aac"
        ),
        "480p": VideoQuality(
            height=480,
            fps=30,
            vcodec="h264",
            acodec="aac"
        )
    }
    
    def __init__(self):
        """Inicializa o downloader."""
        self.video_manager = VideoManager()
        self.youtube = None
        if config.apis.YOUTUBE_API_KEY:
            self.youtube = build(
                "youtube", "v3",
                developerKey=config.apis.YOUTUBE_API_KEY
            )
    
    def _extract_video_id(self, url: str) -> str:
        """
        Extrai ID do vídeo da URL.
        
        Args:
            url: URL do YouTube
            
        Returns:
            ID do vídeo
            
        Raises:
            DownloadError: Se URL inválida
        """
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"youtu\.be\/([0-9A-Za-z_-]{11})",
            r"^([0-9A-Za-z_-]{11})$"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        raise DownloadError(f"URL inválida: {url}")
    
    def _get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        Obtém informações do vídeo via API.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dict com informações
            
        Raises:
            DownloadError: Se erro na API
        """
        if not self.youtube:
            raise DownloadError("API do YouTube não configurada")
            
        try:
            response = self.youtube.videos().list(
                part="snippet,contentDetails",
                id=video_id
            ).execute()
            
            if not response["items"]:
                raise DownloadError(f"Vídeo não encontrado: {video_id}")
                
            return response["items"][0]
            
        except HttpError as e:
            raise DownloadError(f"Erro na API do YouTube: {e.reason}")
    
    def download(
        self,
        url: str,
        quality: str = "1080p",
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Baixa um vídeo do YouTube.
        
        Args:
            url: URL do vídeo
            quality: Qualidade desejada
            output_dir: Diretório de saída
            
        Returns:
            Path do arquivo baixado
            
        Raises:
            DownloadError: Se houver erro no download
        """
        try:
            # Extrai ID e informações
            video_id = self._extract_video_id(url)
            
            # Verifica se já existe
            existing = self.video_manager.get_video(video_id)
            if existing and existing.path.exists():
                logger.info(f"Vídeo já baixado: {video_id}")
                return existing.path
            
            # Obtém informações
            info = self._get_video_info(video_id)
            title = info["snippet"]["title"]
            
            # Configura qualidade
            if quality not in self.QUALITIES:
                raise DownloadError(f"Qualidade inválida: {quality}")
            format_str = self.QUALITIES[quality].to_format()
            
            # Define diretório de saída
            output_dir = output_dir or config.paths.VIDEOS_DIR
            output_path = output_dir / f"{video_id}.mp4"
            
            # Configuração do yt-dlp
            ydl_opts = {
                "format": format_str,
                "outtmpl": str(output_path),
                "merge_output_format": "mp4",
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }],
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "progress_hooks": [self._progress_hook]
            }
            
            # Baixa vídeo
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Registra no gerenciador
            self.video_manager.add_video(
                video_id=video_id,
                title=title,
                path=output_path
            )
            
            return output_path
            
        except Exception as e:
            raise DownloadError(f"Erro ao baixar vídeo: {e}")
    
    def _progress_hook(self, d: Dict[str, Any]):
        """
        Hook para progresso do download.
        
        Args:
            d: Dict com informações do progresso
        """
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            if total > 0:
                downloaded = d.get("downloaded_bytes", 0)
                percent = downloaded / total * 100
                logger.info(f"Download: {percent:.1f}%")
        elif d["status"] == "finished":
            logger.info("Download concluído")
    
    def get_video_url(self, video_id: str) -> str:
        """
        Gera URL para um ID de vídeo.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            URL do vídeo
        """
        return f"https://www.youtube.com/watch?v={video_id}"
