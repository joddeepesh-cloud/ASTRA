import React from 'react';
import type { Observation } from '../types';
import { useObservationImage } from '../hooks/useObservationImage';

interface ObservationImageProps {
  observation: Observation;
  className?: string;
  alt?: string;
}

export const ObservationImage: React.FC<ObservationImageProps> = ({ observation, className = 'w-10 h-10 rounded object-cover border border-slate-700 bg-black', alt }) => {
  const { imageUrl, isLoading } = useObservationImage(observation);

  if (isLoading) {
    return <div className={`${className} bg-slate-950 animate-pulse border border-slate-800`} />;
  }

  return (
    <img
      src={imageUrl}
      alt={alt || observation.id}
      className={className}
    />
  );
};
