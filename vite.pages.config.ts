import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const root = fileURLToPath(new URL("./github-pages-src", import.meta.url));

export default defineConfig({
  base: process.env.PAGES_BASE_PATH ?? "/bb8-do-assembly-guide/",
  root,
  publicDir: false,
  plugins: [react()],
  css: {
    postcss: fileURLToPath(new URL("./", import.meta.url)),
  },
  build: {
    outDir: fileURLToPath(new URL("./pages-dist", import.meta.url)),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL("./github-pages-src/index.html", import.meta.url)),
        en: fileURLToPath(new URL("./github-pages-src/en/index.html", import.meta.url)),
      },
    },
  },
});
