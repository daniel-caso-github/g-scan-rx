import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/extract": "http://app:8000",
      "/verify": "http://app:8000",
      "/process": "http://app:8000",
      "/agent": "http://app:8000",
      "/health": "http://app:8000",
      "/metrics": "http://app:8000",
    },
  },
});
