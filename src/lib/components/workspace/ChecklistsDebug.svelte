<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME } from '$lib/stores';
	
	const i18n = getContext('i18n');
	let loaded = false;
	let debugInfo = '';
	
	onMount(() => {
		console.log('=== i18n Debug Info ===');
		console.log('i18n context:', i18n);
		console.log('i18n type:', typeof i18n);
		console.log('i18n constructor:', i18n?.constructor?.name);
		console.log('$i18n:', $i18n);
		console.log('$i18n type:', typeof $i18n);
		console.log('$i18n.t:', $i18n?.t);
		console.log('$i18n.t type:', typeof $i18n?.t);
		
		debugInfo = `
			i18n context type: ${typeof i18n}
			$i18n type: ${typeof $i18n}
			$i18n.t exists: ${!!$i18n?.t}
			$i18n.t type: ${typeof $i18n?.t}
			$i18n keys: ${$i18n ? Object.keys($i18n).join(', ') : 'none'}
		`;
		
		loaded = true;
	});
	
	// Safe translation function
	const safeT = (key) => {
		try {
			if ($i18n && typeof $i18n.t === 'function') {
				return $i18n.t(key);
			} else {
				console.warn('i18n.t is not available, returning key:', key);
				return key;
			}
		} catch (error) {
			console.error('Translation error:', error);
			return key;
		}
	};
</script>

<svelte:head>
	<title>Checklists Debug • {$WEBUI_NAME}</title>
</svelte:head>

<div class="p-4">
	<h1 class="text-2xl font-bold mb-4">🔧 Checklists i18n Debug</h1>
	
	{#if loaded}
		<div class="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4">
			<h2 class="text-lg font-semibold mb-2">Debug Information:</h2>
			<pre class="text-sm whitespace-pre-wrap">{debugInfo}</pre>
		</div>
		
		<div class="space-y-4">
			<div class="border p-3 rounded">
				<h3 class="font-semibold">Test 1: Direct $i18n.t() call</h3>
				<p>Result: {$i18n.t('Checklists')}</p>
			</div>
			
			<div class="border p-3 rounded">
				<h3 class="font-semibold">Test 2: Safe translation function</h3>
				<p>Result: {safeT('Checklists')}</p>
			</div>
			
			<div class="border p-3 rounded">
				<h3 class="font-semibold">Test 3: Conditional rendering</h3>
				<p>Result: 
					{#if $i18n && $i18n.t}
						{$i18n.t('Checklists')}
					{:else}
						<span class="text-yellow-500">i18n not ready</span>
					{/if}
				</p>
			</div>
			
			<div class="border p-3 rounded">
				<h3 class="font-semibold">Test 4: Raw context data</h3>
				<p>i18n context: {JSON.stringify($i18n, null, 2)}</p>
			</div>
		</div>
		
		<div class="mt-6">
			<a href="/workspace/checklists" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
				← Back to Checklists
			</a>
		</div>
	{:else}
		<p>Loading debug info...</p>
	{/if}
</div>