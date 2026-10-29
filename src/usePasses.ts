import { useEffect, useState } from 'react';
import { latestPasses, type Latest } from './progress';
import { listPasses } from './store/db';

/** The latest pass per unit (one impl's, or all), read when the screen opens. Null while loading. */
export function useLatestPasses(implId?: string): Latest | null {
  const [latest, setLatest] = useState<Latest | null>(null);
  useEffect(() => {
    let live = true;
    listPasses(implId)
      .catch(() => [])
      .then((passes) => live && setLatest(latestPasses(passes)));
    return () => { live = false; };
  }, [implId]);
  return latest;
}
