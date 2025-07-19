import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Badge from './Badge.svelte';

describe('Badge Component', () => {
	it('should render with default props', () => {
		render(Badge);
		const badge = screen.getByText('');
		expect(badge).toBeInTheDocument();
	});

	it('should render with custom content', () => {
		render(Badge, { content: 'Test Badge' });
		const badge = screen.getByText('Test Badge');
		expect(badge).toBeInTheDocument();
	});

	it('should apply default info style', () => {
		render(Badge, { content: 'Info Badge' });
		const badge = screen.getByText('Info Badge');
		expect(badge).toHaveClass('bg-blue-500/20', 'text-blue-700', 'dark:text-blue-200');
	});

	it('should apply success style', () => {
		render(Badge, { type: 'success', content: 'Success Badge' });
		const badge = screen.getByText('Success Badge');
		expect(badge).toHaveClass('bg-green-500/20', 'text-green-700', 'dark:text-green-200');
	});

	it('should apply warning style', () => {
		render(Badge, { type: 'warning', content: 'Warning Badge' });
		const badge = screen.getByText('Warning Badge');
		expect(badge).toHaveClass('bg-yellow-500/20', 'text-yellow-700', 'dark:text-yellow-200');
	});

	it('should apply error style', () => {
		render(Badge, { type: 'error', content: 'Error Badge' });
		const badge = screen.getByText('Error Badge');
		expect(badge).toHaveClass('bg-red-500/20', 'text-red-700', 'dark:text-red-200');
	});

	it('should apply muted style', () => {
		render(Badge, { type: 'muted', content: 'Muted Badge' });
		const badge = screen.getByText('Muted Badge');
		expect(badge).toHaveClass('bg-gray-500/20', 'text-gray-700', 'dark:text-gray-200');
	});

	it('should fallback to info style for unknown type', () => {
		render(Badge, { type: 'unknown', content: 'Unknown Badge' });
		const badge = screen.getByText('Unknown Badge');
		expect(badge).toHaveClass('bg-blue-500/20', 'text-blue-700', 'dark:text-blue-200');
	});

	it('should have correct base classes', () => {
		render(Badge, { content: 'Test Badge' });
		const badge = screen.getByText('Test Badge');
		expect(badge).toHaveClass(
			'text-xs',
			'font-bold',
			'w-fit',
			'px-2',
			'rounded-sm',
			'uppercase',
			'line-clamp-1',
			'mr-0.5'
		);
	});
});