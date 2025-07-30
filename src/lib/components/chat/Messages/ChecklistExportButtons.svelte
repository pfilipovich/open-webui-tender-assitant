<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	
	import { exportToCSV, exportToXLSX, getChecklistStats } from '$lib/utils/export';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import DocumentArrowDown from '$lib/components/icons/DocumentArrowDown.svelte';
	
	const i18n = getContext<Writable<i18nType>>('i18n');

	interface ChecklistResult {
		prompt: string;
		promptTitle?: string;
		promptCommand?: string;
		response: string;
		rawResponse?: string; // Store original JSON
		structured_output?: boolean; // Flag for structured responses
		schema?: string; // Store schema used
		error: boolean;
		validation_error?: string; // Schema validation errors
	}

	export let checklistResults: ChecklistResult[] = [];
	export let isLastMessage = false;
	
	$: hasData = checklistResults && checklistResults.length > 0;
	$: stats = hasData ? getChecklistStats(checklistResults) : null;

	const handleExportCSV = () => {
		if (!hasData) {
			toast.error($i18n?.t?.('No checklist data to export') || 'No checklist data to export');
			return;
		}

		try {
			exportToCSV(checklistResults);
			toast.success($i18n?.t?.('Checklist exported to CSV successfully') || 'Checklist exported to CSV successfully');
		} catch (error) {
			console.error('CSV export error:', error);
			toast.error($i18n?.t?.('Failed to export CSV') || 'Failed to export CSV');
		}
	};

	const handleExportExcel = () => {
		if (!hasData) {
			toast.error($i18n?.t?.('No checklist data to export') || 'No checklist data to export');
			return;
		}

		try {
			exportToXLSX(checklistResults);
			toast.success($i18n?.t?.('Checklist exported to Excel successfully') || 'Checklist exported to Excel successfully');
		} catch (error) {
			console.error('Excel export error:', error);
			toast.error($i18n?.t?.('Failed to export Excel') || 'Failed to export Excel');
		}
	};
</script>

{#if hasData}
	<!-- CSV Export Button -->
	<Tooltip content="{$i18n?.t?.('Export to CSV') || 'Export to CSV'} ({stats?.total} items, {stats?.structured} structured)" placement="bottom">
		<button
			aria-label={$i18n?.t?.('Export to CSV') || 'Export to CSV'}
			class="{isLastMessage ? 'visible' : 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
			on:click={handleExportCSV}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="2"
				stroke="currentColor"
				class="w-4 h-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0-1.125.504-1.125 1.125V11.25a9 9 0 00-9-9z"
				/>
			</svg>
			<span class="text-xs ml-1">CSV</span>
		</button>
	</Tooltip>

	<!-- Excel Export Button -->
	<Tooltip content="{$i18n?.t?.('Export to Excel') || 'Export to Excel'} ({stats?.total} items, {stats?.structured} structured)" placement="bottom">
		<button
			aria-label={$i18n?.t?.('Export to Excel') || 'Export to Excel'}
			class="{isLastMessage ? 'visible' : 'invisible group-hover:visible'} p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
			on:click={handleExportExcel}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="2"
				stroke="currentColor"
				class="w-4 h-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75A1.125 1.125 0 004.5 18.375m-1.125 1.125c0 .621.504 1.125 1.125 1.125h1.5c.621 0 1.125-.504 1.125-1.125M3.375 19.5a1.125 1.125 0 001.125 1.125h7.5"
				/>
			</svg>
			<span class="text-xs ml-1">XLSX</span>
		</button>
	</Tooltip>
{/if}