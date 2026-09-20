import { useState, useEffect } from 'react';
import type { Observation } from '../types';
import libraryData from '../data/observationLibrary.json';
import { getImageBlob } from '../services/imageStore';
import { getAnalysisHistory } from '../services/analysisHistory';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

export function useObservationImage(obs: Observation | null | undefined): { imageUrl: string; isFallback: boolean; isLoading: boolean } {
  const [imageUrl, setImageUrl] = useState<string>(() => obs?.image_url || '');
  const [isFallback, setIsFallback] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!obs) {
      setImageUrl('');
      setIsLoading(false);
      return;
    }

    let createdObjectUrl: string | null = null;
    let isMounted = true;

    async function resolveImage() {
      if (!obs) return;
      setIsLoading(true);
      setIsFallback(false);

      const isDev = import.meta.env.DEV;

      // 0. Canonical Library Observation lookup (always canonical for LIB-* records)
      if (obs.id && obs.id.startsWith('LIB-')) {
        const libMatch = LIBRARY_OBSERVATIONS.find((item) => item.id === obs.id);
        if (libMatch?.image_url) {
          if (isMounted) {
            setImageUrl(libMatch.image_url);
            setIsFallback(false);
            setIsLoading(false);
            if (isDev) {
              console.log(`[ImageResolver] Canonical library match SUCCESS for ${obs.id}:`, libMatch.image_url);
            }
          }
          return;
        }
      }

      // 1. Stable library observation asset (/library/, /assets/, or http:// or https://)
      if (
        obs.image_url &&
        !obs.image_url.includes('USER FILE') &&
        !obs.image_url.startsWith('blob:') &&
        !obs.image_url.startsWith('data:') &&
        (obs.image_url.startsWith('http') || obs.image_url.startsWith('/'))
      ) {
        if (isMounted) {
          setImageUrl(obs.image_url);
          setIsFallback(false);
          setIsLoading(false);
          if (isDev) {
            console.log(`[ImageResolver] Resolved stable library image URL for ${obs.id}:`, obs.image_url);
          }
        }
        return;
      }

      // 2. User-uploaded observation: direct IndexedDB lookup using image_key or IMG-{id}
      const primaryKeys = [
        obs.image_key,
        `IMG-${obs.id}`,
        obs.id?.startsWith('IMG-') ? obs.id : null
      ].filter(Boolean) as string[];

      for (const key of primaryKeys) {
        try {
          const blob = await getImageBlob(key);
          if (blob && isMounted) {
            createdObjectUrl = URL.createObjectURL(blob);
            setImageUrl(createdObjectUrl);
            setIsFallback(false);
            setIsLoading(false);
            if (isDev) {
              console.log(`[ImageResolver] IndexedDB lookup SUCCESS for ${obs.id} via key '${key}' (Blob size: ${blob.size} bytes)`);
            }
            return;
          }
        } catch (err) {
          if (isDev) console.warn(`[ImageResolver] IndexedDB lookup error for key '${key}':`, err);
        }
      }

      // 3. Historical observation: match from analysis history ledger by observation_id or id
      const history = getAnalysisHistory();
      const match = history.find(h => h.observation_id === obs.id || h.id === obs.id);
      if (match) {
        if (match.image_key) {
          try {
            const histBlob = await getImageBlob(match.image_key);
            if (histBlob && isMounted) {
              createdObjectUrl = URL.createObjectURL(histBlob);
              setImageUrl(createdObjectUrl);
              setIsFallback(false);
              setIsLoading(false);
              if (isDev) {
                console.log(`[ImageResolver] History match blob SUCCESS for ${obs.id} (Record: ${match.id}, Key: '${match.image_key}', Blob size: ${histBlob.size} bytes)`);
              }
              return;
            }
          } catch (err) {
            if (isDev) console.warn(`[ImageResolver] History blob fetch error for key '${match.image_key}':`, err);
          }
        }
        if (match.image_url && match.image_url.startsWith('/')) {
          if (isMounted) {
            setImageUrl(match.image_url);
            setIsFallback(false);
            setIsLoading(false);
            if (isDev) {
              console.log(`[ImageResolver] History match URL SUCCESS for ${obs.id}:`, match.image_url);
            }
          }
          return;
        }
      }

      // 4. Fallback to existing valid data URL or temporary blob URL if still mounted
      if (obs.image_url && (obs.image_url.startsWith('data:image') || obs.image_url.startsWith('blob:'))) {
        if (isMounted) {
          setImageUrl(obs.image_url);
          setIsFallback(false);
          setIsLoading(false);
          if (isDev) console.log(`[ImageResolver] Fallback to direct URL string for ${obs.id}`);
        }
        return;
      }

      // 5. Genuinely unavailable
      if (isMounted) {
        setImageUrl(obs.image_url || '');
        setIsFallback(true);
        setIsLoading(false);
        if (isDev) console.warn(`[ImageResolver] Image binary genuinely unavailable for ${obs.id}`);
      }
    }

    resolveImage();

    return () => {
      isMounted = false;
      if (createdObjectUrl) {
        URL.revokeObjectURL(createdObjectUrl);
      }
    };
  }, [obs?.id, obs?.image_url, obs?.image_key]);

  return { imageUrl, isFallback, isLoading };
}

