"""Image management service for animal images."""

import json
import fcntl
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import io

from config import settings


class ImageManagerService:
    """Handles reading, writing, and managing animal images."""

    def __init__(self):
        self.images_json_path = settings.animal_images_absolute
        self.storage_path = settings.image_storage_absolute

        # Ensure directories exist
        self.images_json_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _read_images_json(self) -> Dict:
        """Read animal_images.json with file locking."""
        if not self.images_json_path.exists():
            return {}

        with open(self.images_json_path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return data

    def _write_images_json(self, data: Dict) -> None:
        """Write animal_images.json with file locking."""
        with open(self.images_json_path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def get_all_animals(self) -> Dict:
        """Get all animal image configurations."""
        return self._read_images_json()

    def get_animal(self, name: str) -> Optional[Dict]:
        """Get a specific animal's image configuration."""
        data = self._read_images_json()
        return data.get(name)

    def update_animal(self, name: str, alt: Optional[str] = None,
                     thumbnail: Optional[str] = None,
                     images: Optional[list[str]] = None) -> Dict:
        """Update an animal's image configuration."""
        data = self._read_images_json()

        if name not in data:
            raise ValueError(f"Animal '{name}' not found")

        if alt is not None:
            data[name]["alt"] = alt
        if thumbnail is not None:
            data[name]["thumbnail"] = thumbnail
        if images is not None:
            data[name]["images"] = images

        self._write_images_json(data)
        return data[name]

    def upload_image(self, animal_name: str, image_data: bytes,
                    filename: str, is_thumbnail: bool = False) -> Dict:
        """
        Upload and process an image.

        Args:
            animal_name: Name of the animal
            image_data: Raw image bytes
            filename: Original filename
            is_thumbnail: Whether to generate as thumbnail

        Returns:
            Dict with 'filename', 'url', and optionally 'thumbnail_url'
        """
        # Convert to WebP
        try:
            img = Image.open(io.BytesIO(image_data))

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

        except Exception as e:
            raise ValueError(f"Invalid image format: {str(e)}")

        # Generate filename
        animal_slug = animal_name.lower().replace(' ', '_').replace('-', '_')
        data = self._read_images_json()

        if is_thumbnail:
            base_filename = f"{animal_slug}_thumb.webp"
        else:
            # Find next available number
            existing_images = data.get(animal_name, {}).get("images", [])
            n = 1
            while True:
                base_filename = f"{animal_slug}_{n}.webp"
                url = f"/images/animals/{base_filename}"
                if url not in existing_images:
                    break
                n += 1

        # Save full image
        output_path = self.storage_path / base_filename
        img.save(output_path, "WEBP", quality=85)
        url = f"/images/animals/{base_filename}"

        result = {
            "filename": base_filename,
            "url": url
        }

        # Generate thumbnail if this is a regular image
        if not is_thumbnail:
            thumb_filename = f"{animal_slug}_thumb.webp"
            thumb_path = self.storage_path / thumb_filename

            # Create thumbnail (120x68, crop to fit)
            thumb = img.copy()
            thumb.thumbnail((120, 68), Image.Resampling.LANCZOS)

            # Crop to exact size if needed
            if thumb.size != (120, 68):
                # Calculate crop box to center the image
                left = (thumb.width - 120) // 2
                top = (thumb.height - 68) // 2
                right = left + 120
                bottom = top + 68
                thumb = thumb.crop((left, top, right, bottom))

            thumb.save(thumb_path, "WEBP", quality=85)
            result["thumbnail_url"] = f"/images/animals/{thumb_filename}"

            # Update JSON to add new image
            if animal_name not in data:
                data[animal_name] = {
                    "thumbnail": result["thumbnail_url"],
                    "images": [url],
                    "alt": animal_name
                }
            else:
                if url not in data[animal_name]["images"]:
                    data[animal_name]["images"].append(url)
                data[animal_name]["thumbnail"] = result["thumbnail_url"]

            self._write_images_json(data)

        return result

    def delete_image(self, animal_name: str, filename: str) -> None:
        """
        Delete an image file and update JSON.

        Args:
            animal_name: Name of the animal
            filename: Filename to delete (just the filename, not full path)
        """
        data = self._read_images_json()

        if animal_name not in data:
            raise ValueError(f"Animal '{animal_name}' not found")

        # Remove file
        file_path = self.storage_path / filename
        if file_path.exists():
            file_path.unlink()

        # Update JSON
        url = f"/images/animals/{filename}"
        if url in data[animal_name]["images"]:
            data[animal_name]["images"].remove(url)

        # If this was the thumbnail, clear it
        if data[animal_name]["thumbnail"] == url:
            data[animal_name]["thumbnail"] = ""

        self._write_images_json(data)

    def sync_with_filesystem(self) -> Dict:
        """
        Reconcile JSON with actual files in images directory.

        Returns:
            Dict with sync statistics
        """
        data = self._read_images_json()

        # Get all image files
        webp_files = list(self.storage_path.glob("*.webp"))
        existing_urls = {f"/images/animals/{f.name}" for f in webp_files}

        # Track changes
        added = []
        removed = []

        # Check for files not in JSON
        for file_path in webp_files:
            url = f"/images/animals/{file_path.name}"
            found = False

            for animal_name, config in data.items():
                if url in config["images"] or url == config["thumbnail"]:
                    found = True
                    break

            if not found and not file_path.name.endswith("_thumb.webp"):
                # Try to guess animal name from filename
                parts = file_path.stem.rsplit('_', 1)
                if len(parts) == 2 and parts[1].isdigit():
                    guessed_name = parts[0].replace('_', ' ').title()
                    added.append(url)

        # Check for URLs in JSON that don't have files
        for animal_name, config in data.items():
            for url in config["images"]:
                if url not in existing_urls:
                    removed.append(url)
                    config["images"].remove(url)

            if config["thumbnail"] not in existing_urls:
                removed.append(config["thumbnail"])
                config["thumbnail"] = ""

        self._write_images_json(data)

        return {
            "added": added,
            "removed": removed,
            "total_files": len(webp_files)
        }
