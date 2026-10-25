import assert from "node:assert/strict";
import { gzipSync } from "node:zlib";
import { test } from "node:test";

import { readInt8, readJSON } from "../js/data.js";

const gz = (bytes) => new Response(gzipSync(bytes));

test("readJSON gunzips gzip bodies", async () => {
  assert.deepEqual(await readJSON(gz(Buffer.from('{"é":[1]}'))), { é: [1] });
});

test("readJSON reads bodies the server already decompressed", async () => {
  assert.deepEqual(await readJSON(new Response('{"a":2}')), { a: 2 });
});

test("readInt8 gunzips raw int8 bytes", async () => {
  const out = await readInt8(gz(Buffer.from(Int8Array.from([127, -127, 0]).buffer)));
  assert.deepEqual(Array.from(out), [127, -127, 0]);
});
