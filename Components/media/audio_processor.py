"""
Audio processing module.
"""

import os
import tempfile
from typing import List, Optional, Tuple, Dict
from functools import lru_cache
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import webrtcvad
from scipy import signal
from tqdm import tqdm

from ..core.logger import ComponentLogger
from ..core.exceptions import ProcessingError

logger = ComponentLogger(__name__)

class AudioProcessor:
    """
    Audio processing class with enhanced features for video processing.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        vad_mode: int = 3,
        vad_frame_duration: int = 30,
        min_speech_duration: float = 0.5,
        cache_size: int = 128,
        batch_size: int = 8192
    ):
        """
        Initialize audio processor.
        
        Args:
            sample_rate: Target sample rate
            vad_mode: VAD aggressiveness (0-3)
            vad_frame_duration: VAD frame duration in ms
            min_speech_duration: Minimum speech duration in seconds
            cache_size: Size of LRU cache for processed results
            batch_size: Size of batches for processing large files
        """
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(vad_mode)
        self.frame_duration = vad_frame_duration
        self.min_speech_duration = min_speech_duration
        self.batch_size = batch_size
        self._setup_cache(cache_size)
        
    def _setup_cache(self, cache_size: int) -> None:
        """Setup LRU caches for processed results."""
        self.get_audio_stats = lru_cache(maxsize=cache_size)(self._get_audio_stats_impl)
        self.detect_speech = lru_cache(maxsize=cache_size)(self._detect_speech_impl)
        
    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        format: str = "wav",
        sample_rate: Optional[int] = None,
        channels: int = 1
    ) -> str:
        """
        Extract audio from video with progress tracking.
        
        Args:
            video_path: Path to video file
            output_path: Path to output file (temp if None)
            format: Output format
            sample_rate: Target sample rate (original if None)
            channels: Number of channels
            
        Returns:
            Path to output file
            
        Raises:
            ProcessingError: If error extracting audio
        """
        try:
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, f"audio.{format}")
            
            logger.info("Loading audio...")
            y, sr = librosa.load(
                video_path,
                sr=sample_rate,
                mono=(channels == 1)
            )
            
            logger.info("Saving audio...")
            sf.write(
                output_path,
                y,
                sr,
                format=format,
                subtype='PCM_16'
            )
            
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Error extracting audio: {e}")
            
    def remove_noise(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        noise_reduce_strength: float = 0.75,
        noise_threshold: Optional[float] = None
    ) -> str:
        """
        Remove noise using advanced spectral gating.
        
        Args:
            audio_path: Path to audio file
            output_path: Path to output file (temp if None)
            noise_reduce_strength: Strength of noise reduction (0-1)
            noise_threshold: Manual noise threshold (auto if None)
            
        Returns:
            Path to output file
            
        Raises:
            ProcessingError: If error removing noise
        """
        try:
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, "denoised.wav")
            
            # Load audio in batches for large files
            y, sr = librosa.load(audio_path, sr=None)
            
            # Process in batches
            processed_chunks = []
            for i in tqdm(range(0, len(y), self.batch_size), desc="Removing noise"):
                chunk = y[i:i + self.batch_size]
                
                # Compute spectrogram
                D = librosa.stft(chunk)
                D_mag, D_phase = librosa.magphase(D)
                
                # Estimate noise if not provided
                if noise_threshold is None:
                    noise_thresh = np.median(np.abs(D_mag)) * (1 + noise_reduce_strength)
                else:
                    noise_thresh = noise_threshold
                
                # Apply spectral gating
                mask = librosa.decompose.nn_filter(
                    D_mag,
                    aggregate=np.median,
                    metric='cosine'
                )
                mask = np.minimum(mask, D_mag)
                
                # Soft mask with noise threshold
                soft_mask = librosa.util.softmask(
                    D_mag - mask * noise_reduce_strength,
                    mask,
                    noise_thresh
                )
                
                # Apply mask and reconstruct
                D_denoised = soft_mask * D
                chunk_denoised = librosa.istft(D_denoised)
                processed_chunks.append(chunk_denoised)
            
            # Combine chunks
            y_denoised = np.concatenate(processed_chunks)
            
            # Save denoised audio
            sf.write(
                output_path,
                y_denoised,
                sr,
                subtype='PCM_16'
            )
            
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Error removing noise: {e}")
            
    def normalize_volume(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        target_db: float = -20,
        dynamic_range_db: float = 30
    ) -> str:
        """
        Normalize volume with dynamic range compression.
        
        Args:
            audio_path: Path to audio file
            output_path: Path to output file (temp if None)
            target_db: Target dB level
            dynamic_range_db: Desired dynamic range in dB
            
        Returns:
            Path to output file
            
        Raises:
            ProcessingError: If error normalizing volume
        """
        try:
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, "normalized.wav")
            
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Apply compression
            compressed = audio.compress_dynamic_range(
                threshold=-20,
                ratio=4.0,
                attack=5,
                release=50
            )
            
            # Normalize to target level
            change_in_db = target_db - compressed.dBFS
            normalized = compressed.apply_gain(change_in_db)
            
            # Ensure dynamic range
            peak_db = normalized.max_dBFS
            floor_db = peak_db - dynamic_range_db
            normalized = normalized.apply_gain_stereo(lambda x: max(min(x, peak_db), floor_db))
            
            # Export normalized audio
            normalized.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Error normalizing volume: {e}")
    
    def _detect_speech_impl(
        self,
        audio_path: str,
        output_path: Optional[str] = None
    ) -> List[Tuple[float, float]]:
        """Implementation of speech detection with caching."""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Convert to 16-bit PCM
            samples = np.array(y * 32768, dtype=np.int16)
            
            # Frame the audio
            frame_length = int(self.frame_duration * sr / 1000)
            frames = librosa.util.frame(
                samples,
                frame_length=frame_length,
                hop_length=frame_length
            )
            
            # Detect speech in each frame
            speech_frames = []
            for frame in tqdm(frames.T, desc="Detecting speech"):
                is_speech = self.vad.is_speech(
                    frame.tobytes(),
                    self.sample_rate
                )
                speech_frames.append(is_speech)
            
            # Group consecutive speech frames
            speech_segments = []
            start_frame = None
            
            for i, is_speech in enumerate(speech_frames):
                frame_time = i * self.frame_duration / 1000
                
                if is_speech and start_frame is None:
                    start_frame = frame_time
                elif not is_speech and start_frame is not None:
                    duration = frame_time - start_frame
                    if duration >= self.min_speech_duration:
                        speech_segments.append((start_frame, frame_time))
                    start_frame = None
            
            # Add final segment if needed
            if start_frame is not None:
                frame_time = len(speech_frames) * self.frame_duration / 1000
                duration = frame_time - start_frame
                if duration >= self.min_speech_duration:
                    speech_segments.append((start_frame, frame_time))
            
            # Save speech segments if output path provided
            if output_path is not None:
                # Create silent audio
                duration_ms = int(len(samples) / sr * 1000)
                silent = AudioSegment.silent(duration=duration_ms)
                
                # Add speech segments
                audio = AudioSegment.from_file(audio_path)
                for start, end in speech_segments:
                    start_ms = int(start * 1000)
                    end_ms = int(end * 1000)
                    silent = silent.overlay(
                        audio[start_ms:end_ms],
                        position=start_ms
                    )
                
                # Export audio
                silent.export(output_path, format="wav")
            
            return speech_segments
            
        except Exception as e:
            raise ProcessingError(f"Error detecting speech: {e}")
            
    def _get_audio_stats_impl(
        self,
        audio_path: str
    ) -> Dict[str, float]:
        """Implementation of audio stats with caching."""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Get basic stats
            duration = librosa.get_duration(y=y, sr=sr)
            rms = librosa.feature.rms(y=y)[0]
            
            # Get spectral features
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            # Get rhythm features
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'channels': 1 if y.ndim == 1 else y.shape[0],
                'rms_mean': float(np.mean(rms)),
                'rms_std': float(np.std(rms)),
                'rms_max': float(np.max(rms)),
                'zero_crossings': int(sum(librosa.zero_crossings(y))),
                'spectral_centroid_mean': float(np.mean(spec_cent)),
                'spectral_bandwidth_mean': float(np.mean(spec_bw)),
                'tempo': float(tempo)
            }
            
        except Exception as e:
            raise ProcessingError(f"Error getting audio stats: {e}")
            
    def detect_music(
        self,
        audio_path: str,
        threshold: float = 0.5
    ) -> List[Tuple[float, float]]:
        """
        Detect music segments in audio.
        
        Args:
            audio_path: Path to audio file
            threshold: Detection threshold (0-1)
            
        Returns:
            List of (start_time, end_time) tuples
            
        Raises:
            ProcessingError: If error detecting music
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Compute mel spectrogram
            mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
            
            # Compute onset strength
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Detect tempo and beats
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            
            # Compute harmonic-percussive separation
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # Compute features
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
            
            # Compute music likelihood
            music_likelihood = np.zeros(len(onset_env))
            
            # Strong beats increase likelihood
            beat_mask = np.zeros_like(music_likelihood)
            beat_mask[beats] = 1
            music_likelihood += beat_mask * 0.3
            
            # High spectral contrast increases likelihood
            contrast_mean = np.mean(spectral_contrast, axis=0)
            music_likelihood += librosa.util.normalize(contrast_mean) * 0.3
            
            # Strong harmonic content increases likelihood
            harmonic_energy = librosa.feature.rms(y=y_harmonic)[0]
            music_likelihood += librosa.util.normalize(harmonic_energy) * 0.4
            
            # Find segments above threshold
            music_segments = []
            start_frame = None
            
            for i, likelihood in enumerate(music_likelihood):
                frame_time = librosa.frames_to_time(i, sr=sr)
                
                if likelihood > threshold and start_frame is None:
                    start_frame = frame_time
                elif (likelihood <= threshold or i == len(music_likelihood)-1) and start_frame is not None:
                    music_segments.append((start_frame, frame_time))
                    start_frame = None
            
            return music_segments
            
        except Exception as e:
            raise ProcessingError(f"Error detecting music: {e}")
            
    def split_on_silence(
        self,
        audio_path: str,
        output_dir: Optional[str] = None,
        min_silence_len: int = 1000,
        silence_thresh: int = -50,
        keep_silence: int = 100
    ) -> List[str]:
        """
        Split audio on silence with improved silence detection.
        
        Args:
            audio_path: Path to audio file
            output_dir: Output directory (temp if None)
            min_silence_len: Minimum silence length in ms
            silence_thresh: Silence threshold in dB
            keep_silence: Amount of silence to keep in ms
            
        Returns:
            List of output file paths
            
        Raises:
            ProcessingError: If error splitting audio
        """
        try:
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
            
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Detect silence with improved parameters
            not_silence_ranges = librosa.effects.split(
                np.array(audio.get_array_of_samples()),
                top_db=abs(silence_thresh),
                frame_length=2048,
                hop_length=512
            )
            
            # Convert to milliseconds
            not_silence_ranges = librosa.frames_to_time(
                not_silence_ranges.T,
                sr=audio.frame_rate
            ) * 1000
            
            # Merge segments that are too close
            merged_ranges = []
            current_start = not_silence_ranges[0][0]
            current_end = not_silence_ranges[0][1]
            
            for start, end in not_silence_ranges[1:]:
                if start - current_end < min_silence_len:
                    current_end = end
                else:
                    merged_ranges.append((current_start, current_end))
                    current_start = start
                    current_end = end
            
            merged_ranges.append((current_start, current_end))
            
            # Export segments
            chunk_paths = []
            for i, (start, end) in enumerate(merged_ranges):
                # Add some silence for smooth transitions
                chunk = audio[max(0, start-keep_silence):min(len(audio), end+keep_silence)]
                
                # Fade in/out
                chunk = chunk.fade_in(min(keep_silence, 100)).fade_out(min(keep_silence, 100))
                
                # Export
                chunk_path = os.path.join(output_dir, f"chunk_{i:03d}.wav")
                chunk.export(chunk_path, format="wav")
                chunk_paths.append(chunk_path)
            
            return chunk_paths
            
        except Exception as e:
            raise ProcessingError(f"Error splitting audio: {e}")
