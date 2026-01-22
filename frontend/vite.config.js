import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  plugins: [basicSsl()],

  server: {
    host: 'localhost',
    port: 5173,
    open: true,
    hmr: {
      host: 'localhost',
      port: 5173,
    },
  },

  build: {
    target: 'esnext',
    minify: 'terser',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        // Code splitting for better caching
        manualChunks: {
          phaser: ['phaser'],
          vendor: ['axios', 'ws'],
        },
      },
    },
  },

  resolve: {
    alias: {
      '@': '/src',
      '@scenes': '/src/scenes',
      '@ui': '/src/ui',
      '@api': '/src/api',
      '@utils': '/src/utils',
      '@assets': '/src/assets',
      '@styles': '/src/styles',
    },
  },

  optimizeDeps: {
    include: ['phaser', 'axios', 'ws'],
  },
});
