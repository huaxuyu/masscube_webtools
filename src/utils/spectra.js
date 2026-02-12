export function parseSpectrum(text) {
  if (!text) {
    return [];
  }

  const peaks = [];
  const parts = text.split('|');

  for (let part of parts) {
    part = part.trim();
    if (!part) {
      continue;
    }

    const values = part.split(';');
    if (values.length < 2) {
      continue;
    }

    const mz = parseFloat(values[0]);
    const intensity = parseFloat(values[1]);

    if (!Number.isNaN(mz) && !Number.isNaN(intensity)) {
      peaks.push({ mz, intensity });
    }
  }

  return peaks.sort((a, b) => a.mz - b.mz);
}

export function cosineSimilarityTolerance(a, b, tolerance) {
  if (!a.length || !b.length) {
    return 0;
  }

  const sortedA = [...a].sort((x, y) => y.intensity - x.intensity);
  const sortedB = [...b].sort((x, y) => y.intensity - x.intensity);

  const usedB = new Array(sortedB.length).fill(false);

  let dot = 0;
  let normA = 0;
  let normB = 0;

  for (const peak of sortedA) {
    normA += peak.intensity * peak.intensity;
  }

  for (const peak of sortedB) {
    normB += peak.intensity * peak.intensity;
  }

  if (normA === 0 || normB === 0) {
    return 0;
  }

  for (const peakA of sortedA) {
    let bestIndex = -1;
    let bestIntensity = -1;

    for (let index = 0; index < sortedB.length; index += 1) {
      if (usedB[index]) {
        continue;
      }

      const peakB = sortedB[index];
      if (Math.abs(peakA.mz - peakB.mz) <= tolerance && peakB.intensity > bestIntensity) {
        bestIntensity = peakB.intensity;
        bestIndex = index;
      }
    }

    if (bestIndex !== -1) {
      dot += peakA.intensity * sortedB[bestIndex].intensity;
      usedB[bestIndex] = true;
    }
  }

  return dot / Math.sqrt(normA * normB);
}

export function normalizeMirrorPeaks(a, b) {
  let maxIntensity = 0;

  for (const peak of a) {
    maxIntensity = Math.max(maxIntensity, Math.abs(peak.intensity));
  }

  for (const peak of b) {
    maxIntensity = Math.max(maxIntensity, Math.abs(peak.intensity));
  }

  if (maxIntensity === 0) {
    maxIntensity = 1;
  }

  const buildSticks = (spectrum, direction = 1) => {
    const x = [];
    const y = [];

    for (const peak of spectrum) {
      x.push(peak.mz, peak.mz, null);
      y.push(0, (direction * peak.intensity) / maxIntensity, null);
    }

    return { x, y };
  };

  const top = buildSticks(a, 1);
  const bottom = buildSticks(b, -1);

  return {
    top,
    bottom,
    maxMz: Math.max(0, ...a.map((peak) => peak.mz), ...b.map((peak) => peak.mz)),
  };
}
