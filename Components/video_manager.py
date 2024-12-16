import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from .logger import get_logger
from .exceptions import VideoManagerError

logger = get_logger(__name__)

@dataclass
class VideoMetadata:
    """Metadata for a video"""
    title: str
    path: str
    url: str
    processed: bool = False
    failed: bool = False
    error: Optional[str] = None
    added_at: str = ""
    processed_at: Optional[str] = None
    duration: Optional[float] = None

class VideoManager:
    """Manages downloaded and processed videos state"""
    
    def __init__(self, videos_dir: str = "downloads", db_file: str = "videos.json"):
        """
        Initialize video manager.
        
        Args:
            videos_dir: Directory to store videos
            db_file: File to store video metadata
            
        Raises:
            VideoManagerError: If directories cannot be created or database cannot be loaded
        """
        self.videos_dir = Path(videos_dir)
        self.db_file = Path(db_file)
        self.videos: Dict[str, VideoMetadata] = {}
        
        try:
            self._ensure_dirs()
            self._load_db()
        except Exception as e:
            raise VideoManagerError(f"Failed to initialize VideoManager: {e}")
        
    def _ensure_dirs(self) -> None:
        """Ensure necessary directories exist"""
        try:
            self.videos_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise VideoManagerError(f"Failed to create directory {self.videos_dir}: {e}")
        
    def _load_db(self) -> None:
        """Load videos database"""
        if not self.db_file.exists():
            logger.info(f"Creating new database at {self.db_file}")
            self.videos = {}
            self._save_db()
            return
            
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.videos = {
                    video_id: VideoMetadata(**video_data)
                    for video_id, video_data in data.items()
                }
        except json.JSONDecodeError as e:
            raise VideoManagerError(f"Invalid JSON in database: {e}")
        except Exception as e:
            raise VideoManagerError(f"Failed to load database: {e}")
            
    def _save_db(self) -> None:
        """Save videos database"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                data = {
                    video_id: vars(metadata)
                    for video_id, metadata in self.videos.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise VideoManagerError(f"Failed to save database: {e}")
            
    def add_video(
        self, 
        video_id: str, 
        title: str, 
        path: str, 
        url: str,
        duration: Optional[float] = None
    ) -> None:
        """
        Add a new video to the database.
        
        Args:
            video_id: Video ID
            title: Video title
            path: Video file path
            url: Video URL
            duration: Video duration in seconds
            
        Raises:
            VideoManagerError: If video cannot be added
        """
        try:
            self.videos[video_id] = VideoMetadata(
                title=title,
                path=path,
                url=url,
                added_at=datetime.now().isoformat(),
                duration=duration
            )
            self._save_db()
            logger.info(f"Added video {video_id}: {title}")
        except Exception as e:
            raise VideoManagerError(f"Failed to add video {video_id}: {e}")
        
    def get_unprocessed_videos(self) -> List[tuple[str, str]]:
        """
        Get list of unprocessed videos.
        
        Returns:
            List of tuples (video_path, video_id) for unprocessed videos
        """
        try:
            unprocessed = []
            for video_id, metadata in self.videos.items():
                if not metadata.processed and not metadata.failed:
                    video_path = os.path.join(self.videos_dir, os.path.basename(metadata.path))
                    if os.path.exists(video_path):
                        unprocessed.append((video_path, video_id))
                    else:
                        logger.warning(f"Vídeo não encontrado: {video_path}")
                        
            return unprocessed
            
        except Exception as e:
            logger.error(f"Erro obtendo vídeos não processados: {e}")
            return []
        
    def mark_as_processed(self, video_id: str, error: Optional[str] = None) -> None:
        """
        Mark a video as processed.
        
        Args:
            video_id: Video ID
            error: Optional error message if processing failed
            
        Raises:
            VideoManagerError: If video status cannot be updated
        """
        try:
            if video_id not in self.videos:
                raise VideoManagerError(f"Video {video_id} not found")
                
            self.videos[video_id].processed = True
            self.videos[video_id].processed_at = datetime.now().isoformat()
            
            if error:
                self.videos[video_id].failed = True
                self.videos[video_id].error = error
                logger.error(f"Video {video_id} processing failed: {error}")
            else:
                logger.info(f"Video {video_id} processed successfully")
                
            self._save_db()
        except Exception as e:
            raise VideoManagerError(f"Failed to mark video {video_id} as processed: {e}")
            
    def scan_videos_directory(self) -> None:
        """
        Scan videos directory for new videos.
        
        Raises:
            VideoManagerError: If directory cannot be scanned
        """
        try:
            for file_path in self.videos_dir.glob("*.mp4"):
                video_id = file_path.stem
                if video_id not in self.videos:
                    logger.info(f"Found new video: {video_id}")
                    self.add_video(
                        video_id=video_id,
                        title=video_id,
                        path=str(file_path.relative_to(self.videos_dir)),
                        url=""
                    )
        except Exception as e:
            raise VideoManagerError(f"Failed to scan videos directory: {e}")

    def get_video_path(self, video_id: str) -> str:
        """
        Get the absolute path to a video file.
        
        Args:
            video_id: Video ID
            
        Returns:
            Absolute path to video file
            
        Raises:
            VideoManagerError: If video not found or path is invalid
        """
        try:
            if video_id not in self.videos:
                raise VideoManagerError(f"Video {video_id} not found")
                
            video = self.videos[video_id]
            video_path = self.videos_dir / video.path
            
            if not video_path.exists():
                raise VideoManagerError(f"Video file not found: {video_path}")
                
            return str(video_path.absolute())
            
        except Exception as e:
            raise VideoManagerError(f"Failed to get video path for {video_id}: {e}")
