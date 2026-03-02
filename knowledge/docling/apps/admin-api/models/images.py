"""Image management models."""

from pydantic import BaseModel, Field
from typing import Optional


class AnimalImageConfig(BaseModel):
    """Config for a single animal's images."""
    thumbnail: str
    images: list[str]
    alt: str


class AnimalImagesResponse(BaseModel):
    """Response with all animal images."""
    animals: dict[str, AnimalImageConfig]


class AnimalImageDetail(BaseModel):
    """Detail for a single animal."""
    name: str
    thumbnail: str
    images: list[str]
    alt: str


class ImageUploadResponse(BaseModel):
    """Response after uploading an image."""
    filename: str
    url: str
    thumbnail_url: Optional[str] = None


class UpdateAnimalImagesRequest(BaseModel):
    """Request to update an animal's image config."""
    alt: Optional[str] = None
    thumbnail: Optional[str] = None
    images: Optional[list[str]] = None
