import React, { memo } from 'react';

interface AnimalGridProps {
  onSelectAnimal: (animal: string) => void;
  disabled?: boolean;
}

interface Animal {
  name: string;
  emoji: string;
}

const animals: Animal[] = [
  { name: 'Lion', emoji: '🦁' },
  { name: 'Elephant', emoji: '🐘' },
  { name: 'Giraffe', emoji: '🦒' },
  { name: 'Camel', emoji: '🐫' },
  { name: 'Emu', emoji: '🪿' },
  { name: 'Serval', emoji: '🐆' },
  { name: 'Porcupine', emoji: '🦔' },
  { name: 'Lemur', emoji: '🐒' },
];

const AnimalGrid: React.FC<AnimalGridProps> = memo(({ onSelectAnimal, disabled = false }) => {
  return (
    <div className="w-full max-w-4xl mx-auto px-2 sm:px-4 py-4 sm:py-6">
      <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-leesburg-brown mb-3 sm:mb-4 text-center">
        Pick an animal to learn about!
      </h2>
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
              p-3
              sm:p-4
              md:p-6
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
            <span className="text-3xl sm:text-4xl md:text-5xl" role="img" aria-label={animal.name}>
              {animal.emoji}
            </span>
            <span className="text-sm sm:text-base md:text-lg font-semibold">{animal.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
});

AnimalGrid.displayName = 'AnimalGrid';

export default AnimalGrid;
