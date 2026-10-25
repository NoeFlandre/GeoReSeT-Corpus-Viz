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

// Insertion into a sorted buffer of k: one pass, no full sort (k is small).
export function topK(values, k) {
  const n = Math.min(k, values.length);
  const rows = new Int32Array(n);
  const best = new Float64Array(n).fill(-Infinity);
  for (let i = 0; i < values.length; i++) {
    const x = values[i];
    if (x <= best[n - 1]) continue;
    let j = n - 1;
    for (; j > 0 && best[j - 1] < x; j--) {
      best[j] = best[j - 1];
      rows[j] = rows[j - 1];
    }
    best[j] = x;
    rows[j] = i;
  }
  return { rows: Array.from(rows), scores: Array.from(best) };
}

export function bestPerPolygon(rows, rowScores, polygonOf) {
  const seen = new Set();
  return rows
    .map((row, i) => ({ row, score: rowScores[i] }))
    .filter(({ row }) => !seen.has(polygonOf[row]) && seen.add(polygonOf[row]));
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
