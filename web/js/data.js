// Read the build's files; gunzip only if the server did not already do it.

async function readBytes(response) {
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return bytes;
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

export async function readJSON(response) {
  return JSON.parse(new TextDecoder().decode(await readBytes(response)));
}

export async function readInt8(response) {
  const bytes = await readBytes(response);
  return new Int8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength);
}
