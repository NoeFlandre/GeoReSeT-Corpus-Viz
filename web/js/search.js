// Exact cosine search over int8 unit vectors, and the summaries the map shows.

export function scores(vectors, dims, query) {
  const out = new Float32Array(vectors.length / dims);
  for (let row = 0, offset = 0; row < out.length; row++, offset += dims) {
    let sum = 0;
    for (let d = 0; d < dims; d++) sum += vectors[offset + d] * query[d];
    out[row] = sum / 127;
  }
  return out;
}

export function topK(values, k) {
  const n = Math.min(k, values.length);
  const threshold = Float32Array.from(values).sort()[values.length - n];
  const rows = [];
  for (let i = 0; i < values.length; i++) if (values[i] >= threshold) rows.push(i);
  return rows.sort((a, b) => values[b] - values[a]).slice(0, n);
}

export function bestPerPolygon(rows, values, polygonOf) {
  const seen = new Set();
  return rows
    .filter((row) => !seen.has(polygonOf[row]) && seen.add(polygonOf[row]))
    .map((row) => ({ row, score: values[row] }));
}

export function countBy(keys, top) {
  const counts = new Map();
  for (const key of keys) counts.set(key, (counts.get(key) ?? 0) + 1);
  return [...counts].sort((a, b) => b[1] - a[1]).slice(0, top);
}

export function hexCounts(hits) {
  const cells = new Map();
  for (const { cell, score } of hits) {
    const current = cells.get(cell) ?? { count: 0, score: -Infinity };
    cells.set(cell, { count: current.count + 1, score: Math.max(current.score, score) });
  }
  return cells;
}
