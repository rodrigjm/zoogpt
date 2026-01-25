"""
Image management API endpoints.
"""

from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from auth import get_current_user, User
from models.images import (
    AnimalImagesResponse,
    AnimalImageDetail,
    AnimalImageConfig,
    ImageUploadResponse,
    UpdateAnimalImagesRequest,
)
from services.image_manager import ImageManagerService


router = APIRouter(prefix="/images", tags=["images"])


def get_image_service():
    """Get image manager service instance."""
    return ImageManagerService()


@router.get("/animals", response_model=AnimalImagesResponse)
async def list_animals_images(
    user: User = Depends(get_current_user),
    service: ImageManagerService = Depends(get_image_service),
):
    """List all animals with their image configurations."""
    animals = service.get_all_animals()

    # Convert to response model
    animals_config = {
        name: AnimalImageConfig(**config)
        for name, config in animals.items()
    }

    return AnimalImagesResponse(animals=animals_config)


@router.get("/animals/{name}", response_model=AnimalImageDetail)
async def get_animal_images(
    name: str,
    user: User = Depends(get_current_user),
    service: ImageManagerService = Depends(get_image_service),
):
    """Get image configuration for a specific animal."""
    config = service.get_animal(name)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal '{name}' not found",
        )

    return AnimalImageDetail(
        name=name,
        thumbnail=config["thumbnail"],
        images=config["images"],
        alt=config["alt"],
    )


@router.put("/animals/{name}", response_model=AnimalImageDetail)
async def update_animal_images(
    name: str,
    body: UpdateAnimalImagesRequest,
    user: User = Depends(get_current_user),
    service: ImageManagerService = Depends(get_image_service),
):
    """Update an animal's image configuration (alt text, thumbnail, image order)."""
    try:
        updated = service.update_animal(
            name=name,
            alt=body.alt,
            thumbnail=body.thumbnail,
            images=body.images,
        )

        return AnimalImageDetail(
            name=name,
            thumbnail=updated["thumbnail"],
            images=updated["images"],
            alt=updated["alt"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/animals/{name}/upload", response_model=ImageUploadResponse)
async def upload_animal_image(
    name: str,
    file: UploadFile = File(...),
    is_thumbnail: bool = False,
    user: User = Depends(get_current_user),
    service: ImageManagerService = Depends(get_image_service),
):
    """
    Upload a new image for an animal.

    - Automatically converts to WebP format
    - Generates thumbnail (120x68) if is_thumbnail=False
    - Updates animal_images.json
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read file data
    try:
        image_data = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}",
        )

    # Process and save image
    try:
        result = service.upload_image(
            animal_name=name,
            image_data=image_data,
            filename=file.filename or "upload.jpg",
            is_thumbnail=is_thumbnail,
        )

        return ImageUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}",
        )


@router.delete("/animals/{name}/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal_image(
    name: str,
    filename: str,
    user: User = Depends(get_current_user),
    service: ImageManagerService = Depends(get_image_service),
):
    """Delete an image for an animal."""
    try:
        service.delete_image(animal_name=name, filename=filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}",
        )


@router.post("/sync")
async def sync_images(
    user: User = Depends(get_current_user),
    service: ImageManagerService = Depends(get_image_service),
):
    """
    Reconcile animal_images.json with actual files in the images directory.

    Returns statistics about added/removed entries.
    """
    try:
        result = service.sync_with_filesystem()
        return {
            "ok": True,
            "added": result["added"],
            "removed": result["removed"],
            "total_files": result["total_files"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )
