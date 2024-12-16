"""
AI YouTube Shorts Generator

This script generates YouTube Shorts from long-form videos using AI.
It handles video processing, language detection, and content generation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from moviepy.editor import VideoFileClip
from langdetect import detect

from Components.core.config import config
from Components.core.exceptions import (
    MediaError,
    LanguageError,
    ConfigError
)
from Components.core.logger import ComponentLogger
from Components.language.language_detector import LanguageDetector
from Components.media.media_utils import (
    get_video_features,
    extract_audio,
    extract_frames,
    trim_video
)

logger = ComponentLogger(__name__)

def load_videos(path: str) -> Dict[str, Any]:
    """
    Load video configuration from JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Dictionary with video configuration
        
    Raises:
        ConfigError: If error loading configuration
    """
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        raise ConfigError(f"Error loading video configuration: {e}")

def process_video(
    video_path: str,
    output_path: Optional[str] = None,
    max_duration: int = 60
) -> str:
    """
    Process video for Shorts generation.
    
    Args:
        video_path: Path to input video
        output_path: Optional output path
        max_duration: Maximum duration in seconds
        
    Returns:
        Path to processed video
        
    Raises:
        MediaError: If error processing video
    """
    try:
        # Get video features
        width, height, duration = get_video_features(video_path)
        logger.info(f"Video features: {width}x{height}, {duration:.2f}s")
        
        # Check if video needs processing
        if duration <= max_duration:
            logger.info("Video already within duration limits")
            return video_path
            
        # Extract best segment
        if output_path is None:
            output_path = str(Path(video_path).with_name("short.mp4"))
            
        # For now, just take first segment
        # TODO: Implement smart segment selection
        start_time = 0
        trim_video(video_path, output_path, start_time, start_time + max_duration)
        
        logger.info(f"Video processed and saved to {output_path}")
        return output_path
        
    except Exception as e:
        raise MediaError(f"Error processing video: {e}")

def detect_language(video_path: str) -> str:
    """
    Detect language in video.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Detected language code
        
    Raises:
        LanguageError: If error detecting language
    """
    try:
        # Extract audio for language detection
        audio_path = extract_audio(video_path)
        
        # Initialize detector
        detector = LanguageDetector()
        result = detector.detect_audio(audio_path)
        
        # Clean up
        os.remove(audio_path)
        
        logger.info(f"Detected language: {result.language} ({result.confidence:.2f})")
        return result.language
        
    except Exception as e:
        raise LanguageError(f"Error detecting language: {e}")

def main():
    """Main execution flow."""
    try:
        # Load configuration
        config.load_env()
        
        # Load video list
        videos = load_videos("videos.json")
        
        # Process each video
        for video in videos["videos"]:
            try:
                # Get video path
                video_path = os.path.join(config.paths.BASE_DIR, video["path"])
                if not os.path.exists(video_path):
                    logger.error(f"Video not found: {video_path}")
                    continue
                
                # Process video
                logger.info(f"Processing video: {video_path}")
                processed_path = process_video(
                    video_path,
                    max_duration=config.processing.MAX_VIDEO_LENGTH
                )
                
                # Detect language
                language = detect_language(processed_path)
                if language not in config.processing.SUPPORTED_LANGUAGES:
                    logger.error(f"Unsupported language: {language}")
                    continue
                
                logger.info(f"Successfully processed {video_path}")
                
            except Exception as e:
                logger.error(f"Error processing video: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())