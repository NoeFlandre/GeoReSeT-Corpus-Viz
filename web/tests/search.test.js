import assert from "node:assert/strict";
import { test } from "node:test";

import { bestPerPolygon, countBy, hexCounts, scores, topK } from "../js/search.js";

test("scores are dot products of int8 rows with the query, rescaled", () => {
  const vectors = Int8Array.from([127, 0, 0, 127, 76, 102]);
  const out = scores(vectors, 2, Float32Array.from([0, 1]));
  assert.deepEqual(Array.from(out, (v) => Math.round(v * 100) / 100), [0, 1, 0.8]);
});

test("topK returns the k best indices, best first", () => {
  assert.deepEqual(Array.from(topK(Float32Array.from([0.1, 0.9, 0.5, 0.7]), 2)), [1, 3]);
  assert.equal(topK(Float32Array.from([0.1, 0.2]), 10).length, 2);
});

test("bestPerPolygon keeps the first hit of each polygon", () => {
  const values = [0.7, 0.2, 0.8, 0.6, 0.9];
  const hits = bestPerPolygon([4, 2, 0, 3], values, [0, 1, 1, 0, 0]);
  assert.deepEqual(hits, [{ row: 4, score: 0.9 }, { row: 2, score: 0.8 }]);
});

test("countBy sorts by count, keeps first-seen order on ties, and truncates", () => {
  assert.deepEqual(countBy(["a", "b", "c", "b", "c", "c"], 2), [["c", 3], ["b", 2]]);
  assert.deepEqual(countBy(["x", "y"], 5), [["x", 1], ["y", 1]]);
});

test("hexCounts counts hits per cell and keeps the best score", () => {
  const cells = hexCounts([{ cell: 3, score: 0.5 }, { cell: 3, score: 0.9 }, { cell: 1, score: 0.4 }]);
  assert.deepEqual([...cells], [[3, { count: 2, score: 0.9 }], [1, { count: 1, score: 0.4 }]]);
});
