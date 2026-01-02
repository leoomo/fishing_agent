import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // API 请求代理
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        // WebSocket 需要配置超时
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReqWs', (proxyReq, req, socket, options, head) => {
            // WebSocket 代理启动
          });
        },
      },
    },
  },
  build: {
    // Code splitting optimization
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor splitting - separate large libraries
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-antd': ['antd', '@ant-design/icons'],
          'vendor-redux': ['@reduxjs/toolkit', 'react-redux'],
          'vendor-charts': ['echarts', 'echarts-for-react'],
        },
      },
    },
    // Chunk size warning threshold (500KB)
    chunkSizeWarningLimit: 500,
    // Enable source maps for debugging (disable in production)
    sourcemap: false,
    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console.log in production
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  // Optimize dependency pre-bundling
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      '@ant-design/icons',
      '@reduxjs/toolkit',
      'react-redux',
      'axios',
    ],
  },
})
