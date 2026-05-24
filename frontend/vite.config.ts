import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalized = id.replace(/\\/g, "/");
          if (normalized.includes("/node_modules/react/") || normalized.includes("/node_modules/react-dom/")) {
            return "vendor-react";
          }
          if (normalized.endsWith("/src/api.ts")) {
            return "studio-api";
          }
          if (normalized.endsWith("/src/novelUi.tsx")) {
            return "studio-novel-ui";
          }
          if (normalized.endsWith("/src/tavernUi.tsx")) {
            return "studio-tavern-ui";
          }
          if (normalized.endsWith("/src/worldUi.tsx")) {
            return "studio-world-ui";
          }
          if (normalized.endsWith("/src/providerUi.tsx")) {
            return "studio-provider-ui";
          }
          if (normalized.endsWith("/src/desktopUi.tsx")) {
            return "studio-desktop-ui";
          }
        }
      }
    }
  },
  server: {
    host: "127.0.0.1",
    port: 5173
  }
});
