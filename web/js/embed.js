// Query embeddings in the browser: same ONNX file, pooling and prefix as the Python build.

const TRANSFORMERS = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.1";
let extractor;

export function loadModel(model) {
  extractor ??= import(TRANSFORMERS).then(({ pipeline }) =>
    pipeline("feature-extraction", model, { dtype: "q8" }),
  );
  return extractor;
}

export async function embedQuery(model, text) {
  const run = await loadModel(model);
  const output = await run(`query: ${text}`, { pooling: "mean", normalize: true });
  return output.data;
}
