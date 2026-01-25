import React, { useState } from 'react';
import AnimalImage from './AnimalImage';
import ImageLightbox from './ImageLightbox';

interface AnimalImageGalleryProps {
  images: string[];
  animal: string;
  thumbnail?: string;
  alt?: string;
}

const AnimalImageGallery: React.FC<AnimalImageGalleryProps> = ({
  images,
  animal,
  thumbnail,
  alt
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  // Don't render if no images
  if (!images || images.length === 0) {
    return null;
  }

  const displayImages = thumbnail && !images.includes(thumbnail)
    ? [thumbnail, ...images]
    : images;

  const imageAlt = alt || `${animal} photos`;

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  const handleImageClick = (index: number) => {
    setLightboxIndex(index);
  };

  const handleCloseLightbox = () => {
    setLightboxIndex(null);
  };

  return (
    <div className="mt-3">
      {/* Toggle Button */}
      <button
        onClick={handleToggle}
        className="flex items-center space-x-2 text-leesburg-orange hover:text-leesburg-brown transition-colors text-sm font-medium"
        aria-expanded={isExpanded}
        aria-controls="animal-gallery"
      >
        <span role="img" aria-label="camera">📷</span>
        <span>
          {isExpanded
            ? 'Hide photos'
            : `See ${animal} photos (${displayImages.length})`
          }
        </span>
      </button>

      {/* Gallery Grid */}
      {isExpanded && (
        <div
          id="animal-gallery"
          className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 animate-fadeIn"
        >
          {displayImages.map((imageUrl, index) => (
            <AnimalImage
              key={`${imageUrl}-${index}`}
              src={imageUrl}
              alt={`${imageAlt} ${index + 1}`}
              onClick={() => handleImageClick(index)}
            />
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightboxIndex !== null && (
        <ImageLightbox
          images={displayImages}
          initialIndex={lightboxIndex}
          alt={imageAlt}
          onClose={handleCloseLightbox}
        />
      )}
    </div>
  );
};

export default AnimalImageGallery;
