import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom',
		setupFiles: ['./src/test/setup.ts'],
		globals: true,
		coverage: {
			reporter: ['text', 'html', 'clover', 'json'],
			exclude: [
				'node_modules/',
				'src/test/',
				'**/*.d.ts',
				'**/*.config.*',
				'build/',
				'dist/',
				'cypress/',
				'coverage/',
				'static/',
				'src/lib/i18n/locales/',
			],
		},
	},
	resolve: {
		alias: {
			'$lib': '/src/lib',
			'$app': '/src/app',
		},
	},
});