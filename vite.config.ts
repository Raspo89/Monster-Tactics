import {defineConfig} from 'vite';
export default defineConfig({server:{allowedHosts:['terminal.local']},build:{chunkSizeWarningLimit:1600}});
