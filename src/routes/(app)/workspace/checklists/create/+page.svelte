<script lang="ts">
    import { onMount, getContext } from 'svelte';
    import { goto } from '$app/navigation';
    import { toast } from 'svelte-sonner';
    
    import { createNewChecklist } from '$lib/apis/checklists';
    import { getPrompts } from '$lib/apis/prompts';
    import { prompts } from '$lib/stores';
    import type { ChecklistForm } from '$lib/apis/checklists';
    
    const i18n = getContext('i18n');
    
    let title = '';
    let command = '';
    let description = '';
    let selectedPrompts: { prompt_command: string; order_index: number }[] = [];
    let availablePrompts = [];
    let loading = false;

    $: commandSlug = title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/^-+|-+$/g, '');

    $: if (commandSlug && !command) {
        command = commandSlug;
    }

    const loadPrompts = async () => {
        try {
            const promptList = await getPrompts(localStorage.token);
            prompts.set(promptList);
            availablePrompts = promptList;
        } catch (error) {
            console.error('Error loading prompts:', error);
            toast.error($i18n.t('Failed to load prompts'));
        }
    };

    const addPrompt = (promptCommand: string) => {
        if (selectedPrompts.find(p => p.prompt_command === promptCommand)) {
            return;
        }
        
        selectedPrompts = [
            ...selectedPrompts,
            {
                prompt_command: promptCommand,
                order_index: selectedPrompts.length + 1
            }
        ];
    };

    const removePrompt = (index: number) => {
        selectedPrompts = selectedPrompts.filter((_, i) => i !== index);
        // Re-order remaining prompts
        selectedPrompts = selectedPrompts.map((p, i) => ({
            ...p,
            order_index: i + 1
        }));
    };

    const movePromptUp = (index: number) => {
        if (index === 0) return;
        
        const newPrompts = [...selectedPrompts];
        [newPrompts[index - 1], newPrompts[index]] = [newPrompts[index], newPrompts[index - 1]];
        
        // Update order indices
        selectedPrompts = newPrompts.map((p, i) => ({
            ...p,
            order_index: i + 1
        }));
    };

    const movePromptDown = (index: number) => {
        if (index === selectedPrompts.length - 1) return;
        
        const newPrompts = [...selectedPrompts];
        [newPrompts[index], newPrompts[index + 1]] = [newPrompts[index + 1], newPrompts[index]];
        
        // Update order indices
        selectedPrompts = newPrompts.map((p, i) => ({
            ...p,
            order_index: i + 1
        }));
    };

    const createChecklist = async () => {
        if (!title.trim()) {
            toast.error($i18n.t('Title is required'));
            return;
        }
        
        if (!command.trim()) {
            toast.error($i18n.t('Command is required'));
            return;
        }
        
        if (selectedPrompts.length === 0) {
            toast.error($i18n.t('At least one prompt is required'));
            return;
        }

        loading = true;

        try {
            const checklistData: ChecklistForm = {
                title: title.trim(),
                command: command.trim(),
                description: description.trim() || null,
                access_control: null,
                items: selectedPrompts
            };

            await createNewChecklist(localStorage.token, checklistData);
            toast.success($i18n.t('Checklist created successfully'));
            goto('/workspace/checklists');
        } catch (error) {
            console.error('Error creating checklist:', error);
            toast.error($i18n.t('Failed to create checklist'));
        } finally {
            loading = false;
        }
    };

    onMount(async () => {
        await loadPrompts();
    });
</script>

<svelte:head>
    <title>{$i18n.t('Create Checklist')} | Open WebUI</title>
</svelte:head>

<div class="h-full max-h-full w-full">
    <div class="px-8 py-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
            <div>
                <h1 class="text-2xl font-semibold">{$i18n.t('Create Checklist')}</h1>
                <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">
                    {$i18n.t('Create a new checklist with multiple prompts that can be executed sequentially')}
                </p>
            </div>
            
            <div class="flex items-center space-x-2">
                <a
                    href="/workspace/checklists"
                    class="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                >
                    {$i18n.t('Cancel')}
                </a>
                
                <button
                    on:click={createChecklist}
                    disabled={loading || !title.trim() || !command.trim() || selectedPrompts.length === 0}
                    class="px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-xl hover:bg-gray-800 dark:hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? $i18n.t('Creating...') : $i18n.t('Create Checklist')}
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Left column: Checklist details -->
            <div class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">{$i18n.t('Title')} *</label>
                    <input
                        type="text"
                        placeholder={$i18n.t('Enter checklist title')}
                        bind:value={title}
                        class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>

                <div>
                    <label class="block text-sm font-medium mb-2">{$i18n.t('Command')} *</label>
                    <div class="flex items-center">
                        <span class="text-gray-500 mr-2">%</span>
                        <input
                            type="text"
                            placeholder={$i18n.t('checklist-command')}
                            bind:value={command}
                            class="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {$i18n.t('Used to trigger the checklist in chat (e.g., %meeting-prep)')}
                    </p>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-2">{$i18n.t('Description')}</label>
                    <textarea
                        placeholder={$i18n.t('Optional description of what this checklist does')}
                        bind:value={description}
                        rows="3"
                        class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    ></textarea>
                </div>

                <!-- Available prompts -->
                <div>
                    <label class="block text-sm font-medium mb-2">{$i18n.t('Available Prompts')}</label>
                    <div class="max-h-60 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-xl">
                        {#each availablePrompts as prompt}
                            <button
                                on:click={() => addPrompt(prompt.command)}
                                disabled={selectedPrompts.find(p => p.prompt_command === prompt.command)}
                                class="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 border-b border-gray-200 dark:border-gray-700 last:border-b-0 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <div class="font-medium">{prompt.command}</div>
                                <div class="text-sm text-gray-600 dark:text-gray-400">{prompt.title}</div>
                            </button>
                        {/each}
                    </div>
                </div>
            </div>

            <!-- Right column: Selected prompts -->
            <div>
                <label class="block text-sm font-medium mb-2">
                    {$i18n.t('Selected Prompts')} ({selectedPrompts.length})
                </label>
                
                {#if selectedPrompts.length === 0}
                    <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
                        <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        <p>{$i18n.t('Select prompts from the left to build your checklist')}</p>
                    </div>
                {:else}
                    <div class="space-y-2">
                        {#each selectedPrompts as selectedPrompt, index}
                            {@const prompt = availablePrompts.find(p => p.command === selectedPrompt.prompt_command)}
                            <div class="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
                                <div class="text-sm font-medium text-gray-500 dark:text-gray-400 min-w-[2rem]">
                                    {index + 1}.
                                </div>
                                
                                <div class="flex-1">
                                    <div class="font-medium">{selectedPrompt.prompt_command}</div>
                                    {#if prompt}
                                        <div class="text-sm text-gray-600 dark:text-gray-400">{prompt.title}</div>
                                    {/if}
                                </div>

                                <div class="flex items-center space-x-1">
                                    <button
                                        on:click={() => movePromptUp(index)}
                                        disabled={index === 0}
                                        class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                        title={$i18n.t('Move up')}
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
                                        </svg>
                                    </button>
                                    
                                    <button
                                        on:click={() => movePromptDown(index)}
                                        disabled={index === selectedPrompts.length - 1}
                                        class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                        title={$i18n.t('Move down')}
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                                        </svg>
                                    </button>
                                    
                                    <button
                                        on:click={() => removePrompt(index)}
                                        class="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"
                                        title={$i18n.t('Remove')}
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
    </div>
</div>