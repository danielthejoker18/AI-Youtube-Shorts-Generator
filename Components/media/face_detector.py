"""
Detecção de faces em vídeos.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tempfile

import cv2
import numpy as np
from mediapipe.python.solutions import face_detection
from mediapipe.python.solutions import drawing_utils

from ..core.logger import ComponentLogger
from ..core.exceptions import MediaError

logger = ComponentLogger(__name__)

@dataclass
class FaceBox:
    """Bounding box de face."""
    
    x: float
    y: float
    width: float
    height: float
    confidence: float
    frame_idx: int
    timestamp: float

@dataclass
class FaceTrack:
    """Track de face ao longo do tempo."""
    
    track_id: int
    boxes: List[FaceBox]
    start_time: float
    end_time: float
    avg_confidence: float

class FaceDetector:
    """
    Detector de faces em vídeos.
    """
    
    def __init__(
        self,
        min_confidence: float = 0.5,
        max_faces: int = 5
    ):
        """
        Inicializa detector.
        
        Args:
            min_confidence: Confiança mínima
            max_faces: Máximo de faces
        """
        self.logger = logger
        self.min_confidence = min_confidence
        self.max_faces = max_faces
        
        # Inicializa detector
        self.detector = face_detection.FaceDetection(
            min_detection_confidence=min_confidence,
            model_selection=1  # Modelo mais preciso
        )
    
    def detect_faces(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        save_preview: bool = False,
        sample_rate: int = 1
    ) -> List[FaceTrack]:
        """
        Detecta faces em um vídeo.
        
        Args:
            video_path: Caminho do vídeo
            output_dir: Diretório para preview
            save_preview: Salvar preview
            sample_rate: Taxa de amostragem
            
        Returns:
            Lista de tracks de face
            
        Raises:
            MediaError: Se erro na detecção
        """
        try:
            # Abre vídeo
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise MediaError(f"Erro abrindo vídeo: {video_path}")
            
            # Obtém propriedades
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Prepara preview
            if save_preview and output_dir:
                preview_path = os.path.join(output_dir, "faces_preview.mp4")
                preview = cv2.VideoWriter(
                    preview_path,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (width, height)
                )
            
            # Processa frames
            faces: List[FaceBox] = []
            frame_idx = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Processa apenas alguns frames
                if frame_idx % sample_rate == 0:
                    # Converte para RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Detecta faces
                    results = self.detector.process(frame_rgb)
                    
                    if results.detections:
                        # Processa cada face
                        for detection in results.detections[:self.max_faces]:
                            box = detection.location_data.relative_bounding_box
                            
                            # Converte para coordenadas absolutas
                            x = int(box.xmin * width)
                            y = int(box.ymin * height)
                            w = int(box.width * width)
                            h = int(box.height * height)
                            
                            # Adiciona face
                            faces.append(FaceBox(
                                x=x,
                                y=y,
                                width=w,
                                height=h,
                                confidence=detection.score[0],
                                frame_idx=frame_idx,
                                timestamp=frame_idx/fps
                            ))
                            
                            # Desenha preview
                            if save_preview:
                                cv2.rectangle(
                                    frame,
                                    (x, y),
                                    (x + w, y + h),
                                    (0, 255, 0),
                                    2
                                )
                                cv2.putText(
                                    frame,
                                    f"{detection.score[0]:.2f}",
                                    (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    (0, 255, 0),
                                    2
                                )
                    
                    # Salva frame
                    if save_preview:
                        preview.write(frame)
                
                frame_idx += 1
            
            # Fecha recursos
            cap.release()
            if save_preview:
                preview.release()
            
            # Agrupa faces em tracks
            return self._group_face_tracks(faces)
            
        except Exception as e:
            raise MediaError(f"Erro detectando faces: {e}")
        
        finally:
            if cap is not None:
                cap.release()
            if save_preview and 'preview' in locals():
                preview.release()
    
    def _group_face_tracks(
        self,
        faces: List[FaceBox],
        iou_thresh: float = 0.5,
        time_thresh: float = 0.5
    ) -> List[FaceTrack]:
        """
        Agrupa faces em tracks.
        
        Args:
            faces: Lista de faces
            iou_thresh: Threshold de IoU
            time_thresh: Threshold de tempo
            
        Returns:
            Lista de tracks
        """
        if not faces:
            return []
        
        # Ordena por tempo
        faces.sort(key=lambda x: x.timestamp)
        
        # Inicializa tracks
        tracks: List[FaceTrack] = []
        current_track_id = 0
        
        # Processa cada face
        for face in faces:
            matched = False
            
            # Tenta associar a um track existente
            for track in tracks:
                if not track.boxes:
                    continue
                
                # Obtém última face do track
                last_face = track.boxes[-1]
                
                # Verifica tempo
                time_diff = face.timestamp - last_face.timestamp
                if time_diff > time_thresh:
                    continue
                
                # Calcula IoU
                iou = self._calculate_iou(
                    (last_face.x, last_face.y, last_face.width, last_face.height),
                    (face.x, face.y, face.width, face.height)
                )
                
                # Associa se match
                if iou >= iou_thresh:
                    track.boxes.append(face)
                    track.end_time = face.timestamp
                    track.avg_confidence = np.mean([b.confidence for b in track.boxes])
                    matched = True
                    break
            
            # Cria novo track se não associou
            if not matched:
                tracks.append(FaceTrack(
                    track_id=current_track_id,
                    boxes=[face],
                    start_time=face.timestamp,
                    end_time=face.timestamp,
                    avg_confidence=face.confidence
                ))
                current_track_id += 1
        
        return tracks
    
    def _calculate_iou(
        self,
        box1: Tuple[float, float, float, float],
        box2: Tuple[float, float, float, float]
    ) -> float:
        """
        Calcula IoU entre boxes.
        
        Args:
            box1: (x, y, w, h)
            box2: (x, y, w, h)
            
        Returns:
            IoU score
        """
        # Converte para (x1, y1, x2, y2)
        box1 = (
            box1[0],
            box1[1],
            box1[0] + box1[2],
            box1[1] + box1[3]
        )
        box2 = (
            box2[0],
            box2[1],
            box2[0] + box2[2],
            box2[1] + box2[3]
        )
        
        # Calcula área de intersecção
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calcula áreas
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        # Calcula IoU
        return intersection / float(area1 + area2 - intersection)
    
    def crop_to_face(
        self,
        video_path: str,
        track: FaceTrack,
        output_path: str,
        padding: float = 0.2
    ) -> str:
        """
        Corta vídeo para uma face.
        
        Args:
            video_path: Caminho do vídeo
            track: Track da face
            output_path: Caminho de saída
            padding: Padding relativo
            
        Returns:
            Caminho do vídeo cortado
            
        Raises:
            MediaError: Se erro no corte
        """
        try:
            # Abre vídeo
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise MediaError(f"Erro abrindo vídeo: {video_path}")
            
            # Obtém propriedades
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calcula região média
            boxes = np.array([[b.x, b.y, b.width, b.height] for b in track.boxes])
            mean_box = np.mean(boxes, axis=0)
            
            # Adiciona padding
            pad_x = int(mean_box[2] * padding)
            pad_y = int(mean_box[3] * padding)
            
            crop_x = max(0, int(mean_box[0] - pad_x))
            crop_y = max(0, int(mean_box[1] - pad_y))
            crop_w = min(width - crop_x, int(mean_box[2] + 2 * pad_x))
            crop_h = min(height - crop_y, int(mean_box[3] + 2 * pad_y))
            
            # Prepara writer
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(
                output_path,
                fourcc,
                fps,
                (crop_w, crop_h)
            )
            
            # Processa frames
            frame_idx = 0
            start_frame = int(track.start_time * fps)
            end_frame = int(track.end_time * fps)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Corta apenas frames do track
                if start_frame <= frame_idx <= end_frame:
                    # Corta frame
                    cropped = frame[
                        crop_y:crop_y + crop_h,
                        crop_x:crop_x + crop_w
                    ]
                    
                    # Salva
                    out.write(cropped)
                
                frame_idx += 1
                if frame_idx > end_frame:
                    break
            
            # Fecha recursos
            cap.release()
            out.release()
            
            return output_path
            
        except Exception as e:
            raise MediaError(f"Erro cortando vídeo: {e}")
        
        finally:
            if cap is not None:
                cap.release()
            if 'out' in locals():
                out.release()
