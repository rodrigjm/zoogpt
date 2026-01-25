import React, { useState, useEffect, useRef } from 'react';

interface AnimalImageProps {
  src: string;
  alt: string;
  onClick?: () => void;
}

const AnimalImage: React.FC<AnimalImageProps> = ({ src, alt, onClick }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && imgRef.current && !loaded) {
            const img = imgRef.current;
            img.src = src;
          }
        });
      },
      { rootMargin: '50px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current);
      }
    };
  }, [src, loaded]);

  const handleLoad = () => {
    setLoaded(true);
    setError(false);
  };

  const handleError = () => {
    setError(true);
    setLoaded(true);
  };

  if (error) {
    return (
      <div
        className="relative w-full aspect-video bg-leesburg-beige rounded-lg flex items-center justify-center border border-leesburg-brown/20"
        role="img"
        aria-label={`${alt} (unavailable)`}
      >
        <span className="text-6xl" role="img" aria-label="animal">
          🦁
        </span>
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-video bg-leesburg-beige rounded-lg overflow-hidden">
      {!loaded && (
        <div className="absolute inset-0 animate-pulse bg-leesburg-beige" />
      )}
      <img
        ref={imgRef}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        onClick={onClick}
        className={`
          w-full h-full object-cover cursor-pointer transition-opacity duration-300
          ${loaded ? 'opacity-100' : 'opacity-0'}
          hover:opacity-90
        `}
      />
    </div>
  );
};

export default AnimalImage;
