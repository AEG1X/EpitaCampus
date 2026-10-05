import adapter from "@sveltejs/adapter-static";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    sveltekit({
      // Application monopage : Caddy sert index.html pour toutes les routes.
      adapter: adapter({ fallback: "index.html" }),
    }),
  ],
  server: {
    // En développement, l'API FastAPI tourne sur le port 8000.
    proxy: { "/api": "http://localhost:8000" },
  },
});
