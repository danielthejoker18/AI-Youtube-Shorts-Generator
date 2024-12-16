import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp
from .logger import get_logger

logger = get_logger(__name__)

class YtDlpDownloader:
    def __init__(self, output_dir: str = 'videos', cookies_file: str = 'youtube.cookies'):
        """
        Initialize the downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
            cookies_file: Path to cookies file for authentication
        """
        self.output_dir = Path(output_dir)
        self.cookies_file = Path(cookies_file)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_ydl_opts(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Get yt-dlp options"""
        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'age_limit': 30  # Allow age-restricted videos
        }
        
        # Add cookies if available
        if self.cookies_file.exists():
            opts['cookiefile'] = str(self.cookies_file)
            
        # Add output template if filename provided
        if filename:
            opts['outtmpl'] = str(self.output_dir / filename)
        else:
            opts['outtmpl'] = str(self.output_dir / '%(title)s.%(ext)s')
            
        return opts
        
    def download_video(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a video from YouTube.
        
        Args:
            url: YouTube video URL
            filename: Optional custom filename
            
        Returns:
            str: Path to downloaded video, or None if failed
        """
        try:
            # Get video info first
            with yt_dlp.YoutubeDL(self._get_ydl_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
                
            if not filename:
                filename = f"{info['title']}.mp4"
                
            # Sanitize filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
            if not filename.endswith('.mp4'):
                filename += '.mp4'
                
            # Download video
            logger.info(f"Downloading video: {info['title']}")
            with yt_dlp.YoutubeDL(self._get_ydl_opts(filename)) as ydl:
                ydl.download([url])
                
            output_path = self.output_dir / filename
            if not output_path.exists():
                raise Exception("Download completed but file not found")
                
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return None
            
    def find_viral_video(self) -> Optional[Dict[str, Any]]:
        """
        Find a viral video from YouTube trending page.
        
        Returns:
            dict: Video information or None if no suitable video found
        """
        try:
            trending_url = "https://www.youtube.com/feed/trending"
            
            with yt_dlp.YoutubeDL(self._get_ydl_opts()) as ydl:
                result = ydl.extract_info(trending_url, download=False)
                
            if not result or 'entries' not in result:
                return None
                
            # Filtrar vídeos
            for video in result['entries']:
                # Pular se não tiver todas as informações necessárias
                if not all(k in video for k in ['id', 'title', 'duration']):
                    continue
                    
                # Pular vídeos muito longos ou muito curtos
                duration = video.get('duration', 0)
                if duration < 60 or duration > 1200:  # Entre 1 min e 20 min
                    continue
                    
                # Pular vídeos de música
                if any(tag.lower() in video.get('tags', []) for tag in ['music', 'song', 'clip']):
                    continue
                    
                # Retornar o primeiro vídeo válido
                return {
                    'id': video['id'],
                    'title': video['title'],
                    'url': f"https://www.youtube.com/watch?v={video['id']}",
                    'duration': duration,
                    'view_count': video.get('view_count', 0)
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error finding viral video: {str(e)}")
            return None
