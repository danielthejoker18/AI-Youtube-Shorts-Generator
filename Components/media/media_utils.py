"""
Utility functions for media processing.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip

from ..core.logger import ComponentLogger
from ..core.exceptions import MediaError

logger = ComponentLogger(__name__)

def get_video_features(video_path: str) -> Tuple[int, int, float]:
    """
    Get video features (width, height, duration).
    
    Args:
        video_path: Path to video file
        
    Returns:
        Tuple with width, height and duration
        
    Raises:
        MediaError: If error reading video
    """
    try:
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        cap.release()
        return width, height, duration
    except Exception as e:
        raise MediaError(f"Error reading video features: {e}")

def get_audio_features(audio_path: str) -> float:
    """
    Get audio duration.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Audio duration in seconds
        
    Raises:
        MediaError: If error reading audio
    """
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        audio.close()
        return duration
    except Exception as e:
        raise MediaError(f"Error reading audio features: {e}")

def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """
    Extract audio from video.
    
    Args:
        video_path: Path to video file
        output_path: Optional output path
        
    Returns:
        Path to extracted audio file
        
    Raises:
        MediaError: If error extracting audio
    """
    try:
        if output_path is None:
            output_path = str(Path(video_path).with_suffix('.wav'))
            
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_path)
        video.close()
        
        return output_path
    except Exception as e:
        raise MediaError(f"Error extracting audio: {e}")

def extract_frames(video_path: str, output_dir: str, fps: Optional[float] = None) -> str:
    """
    Extract frames from video.
    
    Args:
        video_path: Path to video file
        output_dir: Output directory
        fps: Optional frames per second
        
    Returns:
        Output directory path
        
    Raises:
        MediaError: If error extracting frames
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        if fps:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps={fps}',
                '-frame_pts', '1',
                os.path.join(output_dir, 'frame_%d.jpg')
            ]
        else:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-frame_pts', '1',
                os.path.join(output_dir, 'frame_%d.jpg')
            ]
            
        subprocess.run(cmd, check=True)
        return output_dir
    except Exception as e:
        raise MediaError(f"Error extracting frames: {e}")

def combine_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Combine audio and video files.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Output path
        
    Returns:
        Output file path
        
    Raises:
        MediaError: If error combining files
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        raise MediaError(f"Error combining audio and video: {e}")

def resize_video(video_path: str, output_path: str, width: int, height: int) -> str:
    """
    Resize video to specified dimensions.
    
    Args:
        video_path: Path to video file
        output_path: Output path
        width: Target width
        height: Target height
        
    Returns:
        Output file path
        
    Raises:
        MediaError: If error resizing video
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'scale={width}:{height}',
            '-c:a', 'copy',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        raise MediaError(f"Error resizing video: {e}")

def crop_video(video_path: str, output_path: str, x: int, y: int, width: int, height: int) -> str:
    """
    Crop video to specified region.
    
    Args:
        video_path: Path to video file
        output_path: Output path
        x: X coordinate
        y: Y coordinate
        width: Region width
        height: Region height
        
    Returns:
        Output file path
        
    Raises:
        MediaError: If error cropping video
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v',
            f'crop={width}:{height}:{x}:{y}',
            '-c:a', 'copy',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        raise MediaError(f"Error cropping video: {e}")

def trim_video(video_path: str, output_path: str, start_time: float, end_time: float) -> str:
    """
    Trim video to specified time range.
    
    Args:
        video_path: Path to video file
        output_path: Output path
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        Output file path
        
    Raises:
        MediaError: If error trimming video
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c:v', 'copy',
            '-c:a', 'copy',
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        raise MediaError(f"Error trimming video: {e}")
