// vitest.config.ts
import { sveltekit } from "file:///mnt/d/open-webui-tender-assitant/node_modules/@sveltejs/kit/src/exports/vite/index.js";
import { defineConfig } from "file:///mnt/d/open-webui-tender-assitant/node_modules/vitest/dist/config.js";
var vitest_config_default = defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}"],
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    coverage: {
      reporter: ["text", "html", "clover", "json"],
      exclude: [
        "node_modules/",
        "src/test/",
        "**/*.d.ts",
        "**/*.config.*",
        "build/",
        "dist/",
        "cypress/",
        "coverage/",
        "static/",
        "src/lib/i18n/locales/"
      ]
    }
  },
  resolve: {
    alias: {
      "$lib": "/src/lib",
      "$app": "/src/app"
    }
  }
});
export {
  vitest_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZXN0LmNvbmZpZy50cyJdLAogICJzb3VyY2VzQ29udGVudCI6IFsiY29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2Rpcm5hbWUgPSBcIi9tbnQvZC9vcGVuLXdlYnVpLXRlbmRlci1hc3NpdGFudFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiL21udC9kL29wZW4td2VidWktdGVuZGVyLWFzc2l0YW50L3ZpdGVzdC5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL21udC9kL29wZW4td2VidWktdGVuZGVyLWFzc2l0YW50L3ZpdGVzdC5jb25maWcudHNcIjtpbXBvcnQgeyBzdmVsdGVraXQgfSBmcm9tICdAc3ZlbHRlanMva2l0L3ZpdGUnO1xuaW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZXN0L2NvbmZpZyc7XG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG5cdHBsdWdpbnM6IFtzdmVsdGVraXQoKV0sXG5cdHRlc3Q6IHtcblx0XHRpbmNsdWRlOiBbJ3NyYy8qKi8qLnt0ZXN0LHNwZWN9Lntqcyx0c30nXSxcblx0XHRlbnZpcm9ubWVudDogJ2pzZG9tJyxcblx0XHRzZXR1cEZpbGVzOiBbJy4vc3JjL3Rlc3Qvc2V0dXAudHMnXSxcblx0XHRnbG9iYWxzOiB0cnVlLFxuXHRcdGNvdmVyYWdlOiB7XG5cdFx0XHRyZXBvcnRlcjogWyd0ZXh0JywgJ2h0bWwnLCAnY2xvdmVyJywgJ2pzb24nXSxcblx0XHRcdGV4Y2x1ZGU6IFtcblx0XHRcdFx0J25vZGVfbW9kdWxlcy8nLFxuXHRcdFx0XHQnc3JjL3Rlc3QvJyxcblx0XHRcdFx0JyoqLyouZC50cycsXG5cdFx0XHRcdCcqKi8qLmNvbmZpZy4qJyxcblx0XHRcdFx0J2J1aWxkLycsXG5cdFx0XHRcdCdkaXN0LycsXG5cdFx0XHRcdCdjeXByZXNzLycsXG5cdFx0XHRcdCdjb3ZlcmFnZS8nLFxuXHRcdFx0XHQnc3RhdGljLycsXG5cdFx0XHRcdCdzcmMvbGliL2kxOG4vbG9jYWxlcy8nLFxuXHRcdFx0XSxcblx0XHR9LFxuXHR9LFxuXHRyZXNvbHZlOiB7XG5cdFx0YWxpYXM6IHtcblx0XHRcdCckbGliJzogJy9zcmMvbGliJyxcblx0XHRcdCckYXBwJzogJy9zcmMvYXBwJyxcblx0XHR9LFxuXHR9LFxufSk7Il0sCiAgIm1hcHBpbmdzIjogIjtBQUF5UixTQUFTLGlCQUFpQjtBQUNuVCxTQUFTLG9CQUFvQjtBQUU3QixJQUFPLHdCQUFRLGFBQWE7QUFBQSxFQUMzQixTQUFTLENBQUMsVUFBVSxDQUFDO0FBQUEsRUFDckIsTUFBTTtBQUFBLElBQ0wsU0FBUyxDQUFDLDhCQUE4QjtBQUFBLElBQ3hDLGFBQWE7QUFBQSxJQUNiLFlBQVksQ0FBQyxxQkFBcUI7QUFBQSxJQUNsQyxTQUFTO0FBQUEsSUFDVCxVQUFVO0FBQUEsTUFDVCxVQUFVLENBQUMsUUFBUSxRQUFRLFVBQVUsTUFBTTtBQUFBLE1BQzNDLFNBQVM7QUFBQSxRQUNSO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsTUFDRDtBQUFBLElBQ0Q7QUFBQSxFQUNEO0FBQUEsRUFDQSxTQUFTO0FBQUEsSUFDUixPQUFPO0FBQUEsTUFDTixRQUFRO0FBQUEsTUFDUixRQUFRO0FBQUEsSUFDVDtBQUFBLEVBQ0Q7QUFDRCxDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
