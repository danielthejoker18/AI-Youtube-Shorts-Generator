"""
Module for downloading videos from various sources with progress tracking and proper error handling.
"""

import os
from typing import Dict, Optional, Union
from pathlib import Path
import yt_dlp
from tqdm import tqdm
from Components.core.exceptions import DownloadError
from Components.core.logger import ComponentLogger

logger = ComponentLogger(__name__)

class VideoDownloader:
    """A class to handle video downloads with progress tracking and proper error handling."""
    
    def __init__(self, output_path: Union[str, Path] = "downloads"):
        """
        Initialize the VideoDownloader with a specified output path.
        
        Args:
            output_path (Union[str, Path]): Directory where downloaded videos will be saved
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    def _create_progress_hook(self, pbar: tqdm):
        """Create a progress hook for yt-dlp that updates our progress bar."""
        def hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes')
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    pbar.total = total
                    pbar.n = downloaded
                    pbar.refresh()
        return hook
        
    def download(self, url: str, output_filename: Optional[str] = None) -> str:
        """
        Download a video from the given URL with progress tracking.
        
        Args:
            url (str): URL of the video to download
            output_filename (Optional[str]): Custom filename for the downloaded video
            
        Returns:
            str: Path to the downloaded video file
            
        Raises:
            DownloadError: If there's an error during download
        """
        try:
            with tqdm(desc="Downloading video", unit='B', unit_scale=True) as pbar:
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': str(self.output_path / (output_filename if output_filename else '%(title)s.%(ext)s')),
                    'merge_output_format': 'mp4',
                    'progress_hooks': [self._create_progress_hook(pbar)],
                }
                
                logger.info(f"Starting download from {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_path = ydl.prepare_filename(info)
                    logger.info(f"Download completed: {video_path}")
                    return video_path
                    
        except Exception as e:
            error_msg = f"Failed to download video: {str(e)}"
            logger.error(error_msg)
            raise DownloadError(error_msg)
            
    def get_info(self, url: str) -> Dict:
        """
        Get information about a video without downloading it.
        
        Args:
            url (str): URL of the video
            
        Returns:
            Dict: Video information including title, duration, etc.
            
        Raises:
            DownloadError: If there's an error getting video information
        """
        try:
            logger.info(f"Fetching video info from {url}")
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_info = {
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'views': info.get('view_count', 0),
                    'likes': info.get('like_count', 0),
                    'url': url
                }
                logger.info(f"Successfully retrieved info for video: {video_info['title']}")
                return video_info
                
        except Exception as e:
            error_msg = f"Failed to get video info: {str(e)}"
            logger.error(error_msg)
            raise DownloadError(error_msg)
