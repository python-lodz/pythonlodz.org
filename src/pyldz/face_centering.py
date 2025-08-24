from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from deepface import DeepFace  # type: ignore
from PIL import Image

log = logging.getLogger(__name__)


class FaceDetectionError(Exception):
    pass


@dataclass(frozen=True)
class _Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)


def _deepface_extract_faces(img: Image.Image) -> list[dict[str, Any]]:
    # DeepFace.extract_faces requires a file path or NumPy array
    if isinstance(img, Image.Image):
        arr = np.array(img.convert("RGB"))
    else:
        arr = img  # assume already ndarray

    return DeepFace.extract_faces(
        img_path=arr,
        detector_backend="opencv",
        enforce_detection=False,
        align=True,
    )  # type: ignore


def _compute_square_crop(
    box: _Box, img_w: int, img_h: int
) -> tuple[int, int, int, int]:
    cx, cy = box.center
    # Square size: take max dimension of face box and add margin factor
    side = int(max(box.w, box.h) * 2.0)
    side = max(1, side)

    half = side // 2
    left = max(0, cx - half)
    top = max(0, cy - half)
    right = min(img_w, left + side)
    bottom = min(img_h, top + side)

    # Adjust if we hit bounds to keep square
    width = right - left
    height = bottom - top
    side = min(width, height)
    right = left + side
    bottom = top + side
    return left, top, right, bottom


def _to_box(face: dict[str, Any]) -> _Box:
    area = face.get("facial_area") or face.get("region") or {}
    return _Box(
        x=int(area.get("x", 0)),
        y=int(area.get("y", 0)),
        w=int(area.get("w", 0)),
        h=int(area.get("h", 0)),
    )


def detect_and_center_square(image: Image.Image) -> Image.Image:
    faces = _deepface_extract_faces(image)
    if not faces:
        raise FaceDetectionError("No face detected")
    if len(faces) > 1:
        raise FaceDetectionError("More than one face detected")

    box = _to_box(faces[0])
    if box.w <= 0 or box.h <= 0:
        raise FaceDetectionError("Invalid face box")

    img_w, img_h = image.size
    crop = _compute_square_crop(box, img_w, img_h)
    cropped = image.crop(crop)

    # Ensure mode supports alpha if original had it
    if image.mode == "RGBA" and cropped.mode != "RGBA":
        cropped = cropped.convert("RGBA")
    return cropped
