"""
Extração de dados do YouTube.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import DownloadError

logger = ComponentLogger(__name__)

@dataclass
class VideoStats:
    """Estatísticas de um vídeo."""
    
    views: int
    likes: Optional[int]
    comments: int
    duration: str
    published_at: datetime

@dataclass
class ChannelInfo:
    """Informações de um canal."""
    
    id: str
    title: str
    description: str
    subscriber_count: Optional[int]
    video_count: int
    view_count: int

class YouTubeScraper:
    """
    Extrai dados do YouTube.
    """
    
    def __init__(self):
        """Inicializa o scraper."""
        if not config.apis.YOUTUBE_API_KEY:
            raise DownloadError("API do YouTube não configurada")
            
        self.youtube = build(
            "youtube", "v3",
            developerKey=config.apis.YOUTUBE_API_KEY
        )
    
    def get_video_stats(self, video_id: str) -> VideoStats:
        """
        Obtém estatísticas de um vídeo.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Estatísticas do vídeo
            
        Raises:
            DownloadError: Se houver erro na API
        """
        try:
            response = self.youtube.videos().list(
                part="statistics,contentDetails,snippet",
                id=video_id
            ).execute()
            
            if not response["items"]:
                raise DownloadError(f"Vídeo não encontrado: {video_id}")
            
            video = response["items"][0]
            stats = video["statistics"]
            
            return VideoStats(
                views=int(stats["viewCount"]),
                likes=int(stats.get("likeCount", 0)) if "likeCount" in stats else None,
                comments=int(stats.get("commentCount", 0)),
                duration=video["contentDetails"]["duration"],
                published_at=datetime.fromisoformat(
                    video["snippet"]["publishedAt"].replace("Z", "+00:00")
                )
            )
            
        except HttpError as e:
            raise DownloadError(f"Erro na API do YouTube: {e.reason}")
    
    def get_channel_info(self, channel_id: str) -> ChannelInfo:
        """
        Obtém informações de um canal.
        
        Args:
            channel_id: ID do canal
            
        Returns:
            Informações do canal
            
        Raises:
            DownloadError: Se houver erro na API
        """
        try:
            response = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()
            
            if not response["items"]:
                raise DownloadError(f"Canal não encontrado: {channel_id}")
            
            channel = response["items"][0]
            stats = channel["statistics"]
            
            return ChannelInfo(
                id=channel["id"],
                title=channel["snippet"]["title"],
                description=channel["snippet"]["description"],
                subscriber_count=(
                    int(stats["subscriberCount"])
                    if "subscriberCount" in stats else None
                ),
                video_count=int(stats["videoCount"]),
                view_count=int(stats["viewCount"])
            )
            
        except HttpError as e:
            raise DownloadError(f"Erro na API do YouTube: {e.reason}")
    
    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Pesquisa vídeos no YouTube.
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            order: Ordenação (date, rating, relevance, title, viewCount)
            
        Returns:
            Lista de vídeos encontrados
            
        Raises:
            DownloadError: Se houver erro na API
        """
        try:
            response = self.youtube.search().list(
                q=query,
                part="id,snippet",
                maxResults=max_results,
                order=order,
                type="video"
            ).execute()
            
            videos = []
            for item in response["items"]:
                if item["id"]["kind"] == "youtube#video":
                    videos.append({
                        "id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                        "channel_id": item["snippet"]["channelId"],
                        "channel_title": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"]
                    })
            
            return videos
            
        except HttpError as e:
            raise DownloadError(f"Erro na API do YouTube: {e.reason}")
    
    def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Obtém comentários de um vídeo.
        
        Args:
            video_id: ID do vídeo
            max_results: Número máximo de comentários
            order: Ordenação (time, relevance)
            
        Returns:
            Lista de comentários
            
        Raises:
            DownloadError: Se houver erro na API
        """
        try:
            response = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                order=order,
                textFormat="plainText"
            ).execute()
            
            comments = []
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": comment["authorDisplayName"],
                    "text": comment["textDisplay"],
                    "likes": comment["likeCount"],
                    "published_at": comment["publishedAt"],
                    "updated_at": comment["updatedAt"]
                })
            
            return comments
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"Comentários desativados para {video_id}")
                return []
            raise DownloadError(f"Erro na API do YouTube: {e.reason}")
    
    def get_related_videos(
        self,
        video_id: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtém vídeos relacionados.
        
        Args:
            video_id: ID do vídeo base
            max_results: Número máximo de resultados
            
        Returns:
            Lista de vídeos relacionados
            
        Raises:
            DownloadError: Se houver erro na API
        """
        try:
            response = self.youtube.search().list(
                part="id,snippet",
                relatedToVideoId=video_id,
                type="video",
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in response["items"]:
                videos.append({
                    "id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    "channel_id": item["snippet"]["channelId"],
                    "channel_title": item["snippet"]["channelTitle"]
                })
            
            return videos
            
        except HttpError as e:
            raise DownloadError(f"Erro na API do YouTube: {e.reason}")
