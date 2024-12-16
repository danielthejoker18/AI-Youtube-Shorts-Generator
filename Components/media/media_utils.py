"""
Utilities for media processing.
"""

import os
import tempfile
import subprocess
from typing import Dict, Optional, Tuple

import numpy as np
import librosa
import ffmpeg
import cv2

from ..core.logger import ComponentLogger
from ..core.exceptions import ProcessingError

logger = ComponentLogger(__name__)

def get_audio_features(
    audio_path: str,
    sample_rate: int = 16000
) -> Tuple[np.ndarray, int]:
    """
    Extract audio features from file.
    
    Args:
        audio_path: Path to audio file
        sample_rate: Target sample rate
        
    Returns:
        Tuple of (audio array, sample rate)
        
    Raises:
        ProcessingError: If error processing audio
    """
    try:
        y, sr = librosa.load(audio_path, sr=sample_rate)
        return y, sr
    except Exception as e:
        raise ProcessingError(f"Error extracting audio features: {e}")

def get_video_info(video_path: str) -> Dict:
    """
    Get video metadata using ffmpeg.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dict with video info
        
    Raises:
        ProcessingError: If error getting video info
    """
    try:
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        return {
            'width': int(video_info['width']),
            'height': int(video_info['height']),
            'duration': float(probe['format']['duration']),
            'fps': eval(video_info['r_frame_rate']),
            'total_frames': int(video_info['nb_frames'])
        }
    except Exception as e:
        raise ProcessingError(f"Error getting video info: {e}")

def extract_frames(
    video_path: str,
    output_dir: Optional[str] = None,
    fps: Optional[float] = None
) -> str:
    """
    Extract frames from video.
    
    Args:
        video_path: Path to video file
        output_dir: Output directory (temp if None)
        fps: Target FPS (original if None)
        
    Returns:
        Path to output directory
        
    Raises:
        ProcessingError: If error extracting frames
    """
    try:
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
            
        # Get video info
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ProcessingError("Could not open video file")
            
        # Get original FPS if not specified
        if fps is None:
            fps = cap.get(cv2.CAP_PROP_FPS)
            
        # Extract frames
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % (cap.get(cv2.CAP_PROP_FPS) / fps) < 1:
                frame_path = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                
            frame_count += 1
            
        cap.release()
        return output_dir
        
    except Exception as e:
        raise ProcessingError(f"Error extracting frames: {e}")

def combine_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    overwrite: bool = True
) -> str:
    """
    Combine audio and video files.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path to output file
        overwrite: Whether to overwrite existing file
        
    Returns:
        Path to output file
        
    Raises:
        ProcessingError: If error combining files
    """
    try:
        # Input streams
        video = ffmpeg.input(video_path)
        audio = ffmpeg.input(audio_path)
        
        # Output stream
        stream = ffmpeg.output(
            video,
            audio,
            output_path,
            acodec='aac',
            vcodec='copy',
            strict='experimental'
        )
        
        # Run ffmpeg
        if overwrite:
            stream = stream.overwrite_output()
        stream.run(capture_stdout=True, capture_stderr=True)
        
        return output_path
        
    except Exception as e:
        raise ProcessingError(f"Error combining audio and video: {e}")

def resize_video(
    video_path: str,
    output_path: str,
    width: int,
    height: int,
    overwrite: bool = True
) -> str:
    """
    Resize video to target dimensions.
    
    Args:
        video_path: Path to video file
        output_path: Path to output file
        width: Target width
        height: Target height
        overwrite: Whether to overwrite existing file
        
    Returns:
        Path to output file
        
    Raises:
        ProcessingError: If error resizing video
    """
    try:
        # Input stream
        stream = ffmpeg.input(video_path)
        
        # Scale video
        stream = ffmpeg.filter(stream, 'scale', width, height)
        
        # Output stream
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec='copy',
            vcodec='libx264'
        )
        
        # Run ffmpeg
        if overwrite:
            stream = stream.overwrite_output()
        stream.run(capture_stdout=True, capture_stderr=True)
        
        return output_path
        
    except Exception as e:
        raise ProcessingError(f"Error resizing video: {e}")

def crop_video(
    video_path: str,
    output_path: str,
    x: int,
    y: int,
    width: int,
    height: int,
    overwrite: bool = True
) -> str:
    """
    Crop video to target dimensions.
    
    Args:
        video_path: Path to video file
        output_path: Path to output file
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Target width
        height: Target height
        overwrite: Whether to overwrite existing file
        
    Returns:
        Path to output file
        
    Raises:
        ProcessingError: If error cropping video
    """
    try:
        # Input stream
        stream = ffmpeg.input(video_path)
        
        # Crop video
        stream = ffmpeg.filter(
            stream,
            'crop',
            width,
            height,
            x,
            y
        )
        
        # Output stream
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec='copy',
            vcodec='libx264'
        )
        
        # Run ffmpeg
        if overwrite:
            stream = stream.overwrite_output()
        stream.run(capture_stdout=True, capture_stderr=True)
        
        return output_path
        
    except Exception as e:
        raise ProcessingError(f"Error cropping video: {e}")

def cut_video(
    video_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    overwrite: bool = True
) -> str:
    """
    Cut video to target duration.
    
    Args:
        video_path: Path to video file
        output_path: Path to output file
        start_time: Start time in seconds
        end_time: End time in seconds
        overwrite: Whether to overwrite existing file
        
    Returns:
        Path to output file
        
    Raises:
        ProcessingError: If error cutting video
    """
    try:
        # Input stream with trim
        stream = ffmpeg.input(
            video_path,
            ss=start_time,
            t=end_time - start_time
        )
        
        # Output stream
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec='copy',
            vcodec='libx264'
        )
        
        # Run ffmpeg
        if overwrite:
            stream = stream.overwrite_output()
        stream.run(capture_stdout=True, capture_stderr=True)
        
        return output_path
        
    except Exception as e:
        raise ProcessingError(f"Error cutting video: {e}")

def add_fade(
    video_path: str,
    output_path: str,
    fade_in: float = 0.5,
    fade_out: float = 0.5,
    overwrite: bool = True
) -> str:
    """
    Add fade in/out effects to video.
    
    Args:
        video_path: Path to video file
        output_path: Path to output file
        fade_in: Fade in duration in seconds
        fade_out: Fade out duration in seconds
        overwrite: Whether to overwrite existing file
        
    Returns:
        Path to output file
        
    Raises:
        ProcessingError: If error adding fade
    """
    try:
        # Get video duration
        info = get_video_info(video_path)
        duration = info['duration']
        
        # Input stream
        stream = ffmpeg.input(video_path)
        
        # Add fades
        if fade_in > 0:
            stream = ffmpeg.filter(
                stream,
                'fade',
                type='in',
                duration=fade_in
            )
        
        if fade_out > 0:
            stream = ffmpeg.filter(
                stream,
                'fade',
                type='out',
                start_time=duration - fade_out,
                duration=fade_out
            )
        
        # Output stream
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec='copy',
            vcodec='libx264'
        )
        
        # Run ffmpeg
        if overwrite:
            stream = stream.overwrite_output()
        stream.run(capture_stdout=True, capture_stderr=True)
        
        return output_path
        
    except Exception as e:
        raise ProcessingError(f"Error adding fade effects: {e}")

def add_zoom(
    video_path: str,
    output_path: str,
    zoom_factor: float = 1.2,
    duration: float = 1.0,
    overwrite: bool = True
) -> str:
    """
    Add zoom effect to video.
    
    Args:
        video_path: Path to video file
        output_path: Path to output file
        zoom_factor: Final zoom factor
        duration: Effect duration in seconds
        overwrite: Whether to overwrite existing file
        
    Returns:
        Path to output file
        
    Raises:
        ProcessingError: If error adding zoom
    """
    try:
        # Input stream
        stream = ffmpeg.input(video_path)
        
        # Add zoom effect
        stream = ffmpeg.filter(
            stream,
            'zoompan',
            z=f'if(between(t,0,{duration}),{zoom_factor}+(1-{zoom_factor})*t/{duration},{zoom_factor})',
            d=1
        )
        
        # Output stream
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec='copy',
            vcodec='libx264'
        )
        
        # Run ffmpeg
        if overwrite:
            stream = stream.overwrite_output()
        stream.run(capture_stdout=True, capture_stderr=True)
        
        return output_path
        
    except Exception as e:
        raise ProcessingError(f"Error adding zoom effect: {e}")
