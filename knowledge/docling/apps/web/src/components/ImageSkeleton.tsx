import React from 'react';

const ImageSkeleton: React.FC = () => {
  return (
    <div
      className="relative w-full aspect-video bg-gradient-to-r from-leesburg-beige via-gray-200 to-leesburg-beige bg-[length:200%_100%] animate-shimmer rounded-lg"
      role="status"
      aria-label="Loading image"
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-12 h-12 rounded-full bg-leesburg-brown/10 animate-pulse" />
      </div>
    </div>
  );
};

export default ImageSkeleton;
