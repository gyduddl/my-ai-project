import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    build:{
        outDir:'build',
    },
    server: {
        proxy: {
            '/download': {
                target: 'http://localhost:8000', // 백엔드 포트로 변경
                changeOrigin: true,
            }
        }
    }
})