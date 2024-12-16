"""
Editor de vídeo para shorts.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tempfile
import subprocess

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

from ..core.logger import ComponentLogger
from ..core.exceptions import MediaError
from .face_detector import FaceTrack

logger = ComponentLogger(__name__)

@dataclass
class VideoSegment:
    """Segmento de vídeo."""
    
    start_time: float
    end_time: float
    video_path: str
    audio_path: Optional[str] = None
    face_track: Optional[FaceTrack] = None

@dataclass
class TextOverlay:
    """Overlay de texto."""
    
    text: str
    start_time: float
    end_time: float
    position: Tuple[str, str] = ("center", "bottom")
    font_size: int = 32
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 2

class VideoEditor:
    """
    Editor de vídeo para shorts.
    """
    
    def __init__(self):
        """Inicializa editor."""
        self.logger = logger
    
    def cut_segment(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """
        Corta segmento de vídeo.
        
        Args:
            video_path: Caminho do vídeo
            start_time: Tempo inicial
            end_time: Tempo final
            output_path: Caminho de saída
            
        Returns:
            Caminho do segmento
            
        Raises:
            MediaError: Se erro no corte
        """
        try:
            # Comando ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-ss", str(start_time),
                "-t", str(end_time - start_time),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-strict", "experimental",
                output_path
            ]
            
            # Executa comando
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro cortando vídeo: {e}")
    
    def add_subtitles(
        self,
        video_path: str,
        subtitles: List[Dict[str, Any]],
        output_path: str,
        font_size: int = 32
    ) -> str:
        """
        Adiciona legendas a um vídeo.
        
        Args:
            video_path: Caminho do vídeo
            subtitles: Lista de legendas
            output_path: Caminho de saída
            font_size: Tamanho da fonte
            
        Returns:
            Caminho do vídeo com legendas
            
        Raises:
            MediaError: Se erro nas legendas
        """
        try:
            # Carrega vídeo
            video = VideoFileClip(video_path)
            
            # Cria clips de texto
            text_clips = []
            for sub in subtitles:
                clip = TextClip(
                    sub["text"],
                    fontsize=font_size,
                    color="white",
                    stroke_color="black",
                    stroke_width=2,
                    font="Arial"
                )
                
                # Posiciona na parte inferior
                clip = clip.set_position(("center", "bottom"))
                
                # Define duração
                clip = clip.set_start(sub["start"])
                clip = clip.set_duration(sub["end"] - sub["start"])
                
                text_clips.append(clip)
            
            # Combina vídeo e legendas
            final = CompositeVideoClip([video] + text_clips)
            
            # Salva
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac"
            )
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro adicionando legendas: {e}")
    
    def apply_zoom(
        self,
        video_path: str,
        output_path: str,
        zoom_factor: float = 1.5,
        duration: float = 1.0
    ) -> str:
        """
        Aplica zoom dinâmico.
        
        Args:
            video_path: Caminho do vídeo
            output_path: Caminho de saída
            zoom_factor: Fator de zoom
            duration: Duração do zoom
            
        Returns:
            Caminho do vídeo com zoom
            
        Raises:
            MediaError: Se erro no zoom
        """
        try:
            # Carrega vídeo
            video = VideoFileClip(video_path)
            
            def zoom(image, factor):
                """Aplica zoom em uma imagem."""
                h, w = image.shape[:2]
                M = cv2.getRotationMatrix2D((w/2, h/2), 0, factor)
                return cv2.warpAffine(image, M, (w, h))
            
            # Função de zoom suave
            def get_zoom_factor(t):
                """Retorna fator de zoom para tempo t."""
                if t < duration:
                    return 1 + (zoom_factor - 1) * (t / duration)
                return zoom_factor
            
            # Aplica zoom
            zoomed = video.fl_image(
                lambda img: zoom(img, get_zoom_factor(video.duration))
            )
            
            # Salva
            zoomed.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac"
            )
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro aplicando zoom: {e}")
    
    def add_transition(
        self,
        video1_path: str,
        video2_path: str,
        output_path: str,
        transition: str = "fade",
        duration: float = 0.5
    ) -> str:
        """
        Adiciona transição entre vídeos.
        
        Args:
            video1_path: Primeiro vídeo
            video2_path: Segundo vídeo
            output_path: Caminho de saída
            transition: Tipo de transição
            duration: Duração da transição
            
        Returns:
            Caminho do vídeo com transição
            
        Raises:
            MediaError: Se erro na transição
        """
        try:
            # Carrega vídeos
            clip1 = VideoFileClip(video1_path)
            clip2 = VideoFileClip(video2_path)
            
            # Aplica transição
            if transition == "fade":
                # Crossfade
                clip1 = clip1.crossfadein(duration)
                clip2 = clip2.crossfadeout(duration)
            elif transition == "slide":
                # Slide
                w = clip1.w
                clip2 = clip2.set_position(
                    lambda t: (w * (1 - t/duration), 0) if t < duration else (0, 0)
                )
            
            # Combina clips
            final = CompositeVideoClip([clip1, clip2])
            
            # Salva
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac"
            )
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro adicionando transição: {e}")
    
    def create_short(
        self,
        segments: List[VideoSegment],
        output_path: str,
        subtitles: Optional[List[Dict[str, Any]]] = None,
        transitions: bool = True,
        zoom: bool = True
    ) -> str:
        """
        Cria short a partir de segmentos.
        
        Args:
            segments: Lista de segmentos
            output_path: Caminho de saída
            subtitles: Lista de legendas
            transitions: Usar transições
            zoom: Usar zoom dinâmico
            
        Returns:
            Caminho do short
            
        Raises:
            MediaError: Se erro na criação
        """
        try:
            # Diretório temporário
            with tempfile.TemporaryDirectory() as temp_dir:
                processed_segments = []
                
                # Processa cada segmento
                for i, segment in enumerate(segments):
                    # Corta segmento
                    cut_path = os.path.join(temp_dir, f"cut_{i}.mp4")
                    self.cut_segment(
                        segment.video_path,
                        segment.start_time,
                        segment.end_time,
                        cut_path
                    )
                    
                    # Aplica zoom se necessário
                    if zoom:
                        zoom_path = os.path.join(temp_dir, f"zoom_{i}.mp4")
                        self.apply_zoom(cut_path, zoom_path)
                        processed_segments.append(zoom_path)
                    else:
                        processed_segments.append(cut_path)
                
                # Adiciona transições
                if transitions and len(processed_segments) > 1:
                    with_transitions = []
                    for i in range(len(processed_segments) - 1):
                        trans_path = os.path.join(temp_dir, f"trans_{i}.mp4")
                        self.add_transition(
                            processed_segments[i],
                            processed_segments[i + 1],
                            trans_path
                        )
                        with_transitions.append(trans_path)
                    processed_segments = with_transitions
                
                # Combina segmentos
                if len(processed_segments) > 1:
                    # Usa ffmpeg concat
                    with open(os.path.join(temp_dir, "list.txt"), "w") as f:
                        for p in processed_segments:
                            f.write(f"file '{p}'\n")
                    
                    combined_path = os.path.join(temp_dir, "combined.mp4")
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", os.path.join(temp_dir, "list.txt"),
                        "-c", "copy",
                        combined_path
                    ], check=True)
                else:
                    combined_path = processed_segments[0]
                
                # Adiciona legendas
                if subtitles:
                    self.add_subtitles(
                        combined_path,
                        subtitles,
                        output_path
                    )
                else:
                    # Copia para output
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-i", combined_path,
                        "-c", "copy",
                        output_path
                    ], check=True)
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro criando short: {e}")
    
    def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        volume: float = 0.3
    ) -> str:
        """
        Adiciona música de fundo.
        
        Args:
            video_path: Caminho do vídeo
            music_path: Caminho da música
            output_path: Caminho de saída
            volume: Volume da música
            
        Returns:
            Caminho do vídeo com música
            
        Raises:
            MediaError: Se erro na música
        """
        try:
            # Carrega vídeo e música
            video = VideoFileClip(video_path)
            music = VideoFileClip(music_path).audio
            
            # Ajusta duração da música
            if music.duration > video.duration:
                music = music.subclip(0, video.duration)
            else:
                # Loop se necessário
                repeats = int(np.ceil(video.duration / music.duration))
                music = music.loop(repeats)
                music = music.subclip(0, video.duration)
            
            # Ajusta volume
            music = music.volumex(volume)
            
            # Combina áudios
            final_audio = CompositeVideoClip([
                video.set_audio(video.audio),
                video.set_audio(music)
            ]).audio
            
            # Adiciona ao vídeo
            final = video.set_audio(final_audio)
            
            # Salva
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac"
            )
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro adicionando música: {e}")
    
    def export_for_shorts(
        self,
        video_path: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
        fps: int = 60,
        bitrate: str = "2M"
    ) -> str:
        """
        Exporta vídeo no formato Shorts.
        
        Args:
            video_path: Caminho do vídeo
            output_path: Caminho de saída
            width: Largura do vídeo
            height: Altura do vídeo
            fps: FPS do vídeo
            bitrate: Bitrate do vídeo
            
        Returns:
            Caminho do vídeo exportado
            
        Raises:
            MediaError: Se erro na exportação
        """
        try:
            # Carrega vídeo
            clip = VideoFileClip(video_path)
            
            # Redimensiona mantendo aspect ratio
            if clip.w / clip.h > width / height:
                # Limita por altura
                new_width = int(clip.w * height / clip.h)
                resized = clip.resize(height=height)
                # Centraliza horizontalmente
                x = (new_width - width) // 2
                cropped = resized.crop(
                    x1=x,
                    y1=0,
                    x2=x + width,
                    y2=height
                )
            else:
                # Limita por largura
                new_height = int(clip.h * width / clip.w)
                resized = clip.resize(width=width)
                # Centraliza verticalmente
                y = (new_height - height) // 2
                cropped = resized.crop(
                    x1=0,
                    y1=y,
                    x2=width,
                    y2=y + height
                )
            
            # Exporta
            cropped.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=fps,
                bitrate=bitrate
            )
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro exportando vídeo: {e}")
