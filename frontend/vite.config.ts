import {defineConfig} from 'vite';
export default defineConfig({server:{host:'127.0.0.1',proxy:{'/api':{target:'http://localhost:8000',changeOrigin:true},'/media':{target:'http://localhost:8000',changeOrigin:true}}}});
