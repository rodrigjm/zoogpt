import React, { memo } from 'react';

interface AnimalGridProps {
  onSelectAnimal: (animal: string) => void;
  disabled?: boolean;
}

interface Animal {
  name: string;
  thumb: string;
}

const animals: Animal[] = [
  { name: 'Poison Dart Frog', thumb: '/images/animals/poison_dart_frog_1.webp' },
  { name: 'Zebra', thumb: '/images/animals/zebra_1.webp' },
  { name: 'Red Macaw', thumb: '/images/animals/macaw_1.webp' },
  { name: 'Camel', thumb: '/images/animals/camel_1.webp' },
  { name: 'Emu', thumb: '/images/animals/emu_1.webp' },
  { name: 'Serval', thumb: '/images/animals/serval_1.webp' },
  { name: 'Porcupine', thumb: '/images/animals/porcupine_1.webp' },
  { name: 'Lemur', thumb: '/images/animals/lemur_1.webp' },
];

const AnimalGrid: React.FC<AnimalGridProps> = memo(({ onSelectAnimal, disabled = false }) => {
  return (
    <div className="w-full max-w-4xl mx-auto px-2 sm:px-4 py-4 sm:py-6">
      <div
        role="group"
        aria-label="Animal selection buttons"
        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-3 md:gap-4"
      >
        {animals.map((animal) => (
          <button
            key={animal.name}
            onClick={() => !disabled && onSelectAnimal(animal.name)}
            disabled={disabled}
            aria-label={`Learn about ${animal.name}`}
            className={`
              bg-leesburg-beige
              text-leesburg-brown
              rounded-xl
              sm:rounded-2xl
              shadow-md
              transition-all
              duration-200
              overflow-hidden
              flex
              flex-col
              items-center
              justify-center
              gap-1
              sm:gap-2
              border-2
              border-transparent
              focus:outline-none
              focus:ring-4
              focus:ring-leesburg-orange/30
              ${
                disabled
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:bg-leesburg-orange hover:text-white hover:shadow-lg hover:border-leesburg-orange active:scale-95 cursor-pointer'
              }
            `}
          >
            <img
              src={animal.thumb}
              alt={animal.name}
              className="w-full aspect-square object-cover"
              loading="lazy"
            />
            <span className="text-sm sm:text-base md:text-lg font-semibold pb-2 sm:pb-3">{animal.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
});

AnimalGrid.displayName = 'AnimalGrid';

export default AnimalGrid;
