import {defineConfig} from 'vite';
export default defineConfig({build:{rollupOptions:{output:{manualChunks:{react:['react','react-dom','react-dom/client']}}}},server:{host:'127.0.0.1',proxy:{'/api':{target:'http://localhost:8000',changeOrigin:true},'/media':{target:'http://localhost:8000',changeOrigin:true}}}});
