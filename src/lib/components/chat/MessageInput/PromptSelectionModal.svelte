<script lang="ts">
  import { createEventDispatcher, getContext } from 'svelte';
  import { prompts } from '$lib/stores';
  import { flyAndScale } from '$lib/utils/transitions';

  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  export let show = false;

  let searchQuery = '';
  let selectedPromptIdx = 0;

  $: filteredPrompts = ($prompts || [])
    .filter((p) => {
      const query = searchQuery.toLowerCase();
      return (
        p.title.toLowerCase().includes(query) ||
        p.command.toLowerCase().includes(query) ||
        (p.content && p.content.toLowerCase().includes(query))
      );
    })
    .sort((a, b) => a.title.localeCompare(b.title));

  $: if (searchQuery) {
    selectedPromptIdx = 0;
  }

  const handleKeydown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedPromptIdx = Math.min(selectedPromptIdx + 1, filteredPrompts.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedPromptIdx = Math.max(0, selectedPromptIdx - 1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredPrompts[selectedPromptIdx]) {
        selectPrompt(filteredPrompts[selectedPromptIdx]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  const selectPrompt = (prompt) => {
    dispatch('select', prompt);
    show = false;
    searchQuery = '';
  };

  const handleCancel = () => {
    dispatch('cancel');
    show = false;
    searchQuery = '';
  };

  // Reset state when modal opens
  $: if (show) {
    searchQuery = '';
    selectedPromptIdx = 0;
  }
</script>

{#if show}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
       transition:flyAndScale
       on:click={handleCancel}>
    <div class="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col"
         on:click|stopPropagation>
      
      <!-- Header -->
      <div class="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
          {$i18n.t('Select Prompt to Attach')}
        </h2>
        <button on:click={handleCancel} 
                class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Search -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <input
          type="text"
          bind:value={searchQuery}
          placeholder={$i18n.t('Search prompts...')}
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          on:keydown={handleKeydown}
          autofocus
        />
      </div>

      <!-- Prompt List -->
      <div class="flex-1 overflow-y-auto p-2">
        {#if filteredPrompts.length === 0}
          <div class="text-center py-8 text-gray-500 dark:text-gray-400">
            {#if ($prompts || []).length === 0}
              {$i18n.t('No prompts available')}
            {:else}
              {$i18n.t('No prompts match your search')}
            {/if}
          </div>
        {:else}
          {#each filteredPrompts as prompt, idx}
            <button
              class="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 
                     {idx === selectedPromptIdx ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : ''}"
              on:click={() => selectPrompt(prompt)}
            >
              <div class="flex items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="font-medium text-gray-900 dark:text-white truncate">
                      {prompt.title || prompt.name}
                    </h3>
                    {#if prompt.structured_output}
                      <span class="flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-800/30 rounded text-xs text-blue-700 dark:text-blue-300">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                        </svg>
                        SO
                      </span>
                    {/if}
                  </div>
                  <p class="text-sm text-purple-600 dark:text-purple-400 mt-1">
                    {prompt.command}
                  </p>
                  {#if prompt.content}
                    <p class="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                      {prompt.content.replace(/\{\{[^}]*\}\}/g, '').trim().substring(0, 150)}{prompt.content.length > 150 ? '...' : ''}
                    </p>
                  {/if}
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-400 flex-shrink-0">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </div>
            </button>
          {/each}
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          on:click={handleCancel}
          class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          {$i18n.t('Cancel')}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>