import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import Spinner from './Spinner.svelte';

describe('Spinner Component', () => {
	it('should render with default className', () => {
		const { container } = render(Spinner);
		const svg = container.querySelector('svg');
		expect(svg).toBeInTheDocument();
		expect(svg).toHaveClass('size-5');
	});

	it('should render with custom className', () => {
		const { container } = render(Spinner, { className: 'custom-size' });
		const svg = container.querySelector('svg');
		expect(svg).toBeInTheDocument();
		expect(svg).toHaveClass('custom-size');
	});

	it('should have correct structure', () => {
		const { container } = render(Spinner);
		
		// Check wrapper div
		const wrapper = container.querySelector('div');
		expect(wrapper).toHaveClass('flex', 'justify-center', 'text-center');
		
		// Check SVG element
		const svg = container.querySelector('svg');
		expect(svg).toBeInTheDocument();
		expect(svg).toHaveAttribute('viewBox', '0 0 24 24');
		expect(svg).toHaveAttribute('fill', 'currentColor');
		expect(svg).toHaveAttribute('xmlns', 'http://www.w3.org/2000/svg');
	});

	it('should contain animation styles', () => {
		const { container } = render(Spinner);
		const style = container.querySelector('style');
		expect(style).toBeInTheDocument();
		expect(style?.textContent).toContain('spinner_ajPY');
		expect(style?.textContent).toContain('transform-origin: center');
		expect(style?.textContent).toContain('animation: spinner_AtaB 0.75s infinite linear');
		expect(style?.textContent).toContain('@keyframes spinner_AtaB');
		expect(style?.textContent).toContain('transform: rotate(360deg)');
	});

	it('should have correct SVG paths', () => {
		const { container } = render(Spinner);
		const paths = container.querySelectorAll('path');
		expect(paths).toHaveLength(2);
		
		// Check first path (background circle)
		const backgroundPath = paths[0];
		expect(backgroundPath).toHaveAttribute('opacity', '.25');
		expect(backgroundPath).toHaveAttribute('d', 'M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z');
		
		// Check second path (spinning arc)
		const spinningPath = paths[1];
		expect(spinningPath).toHaveClass('spinner_ajPY');
		expect(spinningPath).toHaveAttribute('d', 'M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z');
	});

	it('should be accessible', () => {
		const { container } = render(Spinner);
		const svg = container.querySelector('svg');
		expect(svg).toBeInTheDocument();
		// SVG should be perceivable by screen readers
		expect(svg).toHaveAttribute('fill', 'currentColor');
	});
});