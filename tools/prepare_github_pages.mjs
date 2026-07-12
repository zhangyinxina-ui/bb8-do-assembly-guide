import { cp, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = path.join(root, "public");
const output = path.join(root, "pages-dist");

await cp(source, output, {
  recursive: true,
  filter: (entry) => !entry.endsWith(".blend"),
});
await writeFile(path.join(output, ".nojekyll"), "", "utf8");
console.log(`PREPARED ${output}`);
