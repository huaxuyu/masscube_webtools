export function parseRtIntensityPairs(raw) {
  if (!raw) {
    return [];
  }

  return raw
    .trim()
    .split('|')
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((pair) => {
      const [rt, intensity] = pair
        .split(';')
        .map((value) => Number(String(value).trim()));

      return { rt, intensity };
    })
    .filter((point) => Number.isFinite(point.rt) && Number.isFinite(point.intensity))
    .sort((a, b) => a.rt - b.rt);
}

export function toPeakCsv(rows) {
  const header = 'rt,intensity';
  const body = rows.map((row) => `${row.rt},${row.intensity}`);
  return [header, ...body].join('\n');
}
