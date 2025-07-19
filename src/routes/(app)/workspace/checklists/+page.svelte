<script lang="ts">
    import { onMount, getContext } from 'svelte';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { toast } from 'svelte-sonner';
    
    import { checklists, user } from '$lib/stores';
    import { getChecklistList, deleteChecklistByCommand } from '$lib/apis/checklists';
    import type { ChecklistUserResponse } from '$lib/apis/checklists';
    
    import Spinner from '$lib/components/common/Spinner.svelte';
    
    const i18n = getContext('i18n');
    
    let filteredChecklists: ChecklistUserResponse[] = [];
    let searchQuery = '';
    let loading = false;

    $: filteredChecklists = $checklists.filter((checklist) =>
        checklist.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        checklist.command.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (checklist.description && checklist.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const loadChecklists = async () => {
        loading = true;
        try {
            const checklistList = await getChecklistList(localStorage.token);
            checklists.set(checklistList);
        } catch (error) {
            console.error('Error loading checklists:', error);
            toast.error($i18n.t('Failed to load checklists'));
        }
        loading = false;
    };

    const deleteChecklist = async (checklist: ChecklistUserResponse) => {
        if (!confirm($i18n.t('Are you sure you want to delete this checklist?'))) {
            return;
        }

        try {
            await deleteChecklistByCommand(localStorage.token, checklist.command);
            await loadChecklists();
            toast.success($i18n.t('Checklist deleted successfully'));
        } catch (error) {
            console.error('Error deleting checklist:', error);
            toast.error($i18n.t('Failed to delete checklist'));
        }
    };

    onMount(async () => {
        await loadChecklists();
    });
</script>

<svelte:head>
    <title>{$i18n.t('Checklists')} | Open WebUI</title>
</svelte:head>

<div class="h-full max-h-full w-full space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <div class="text-2xl font-semibold">{$i18n.t('Checklists')}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
                {filteredChecklists.length} {$i18n.t('items')}
            </div>
        </div>
        
        <div class="flex items-center space-x-2">
            <a
                class="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition text-sm font-medium"
                href="/workspace/checklists/create"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    class="w-4 h-4"
                >
                    <path
                        d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z"
                    />
                </svg>
                <div class="ml-1">{$i18n.t('Create Checklist')}</div>
            </a>
        </div>
    </div>

    <!-- Search -->
    <div class="flex flex-col lg:flex-row lg:space-x-4 space-y-3 lg:space-y-0">
        <div class="flex-1">
            <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg
                        class="w-4 h-4 text-gray-400"
                        aria-hidden="true"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 20 20"
                    >
                        <path
                            stroke="currentColor"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"
                        />
                    </svg>
                </div>
                <input
                    class="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-850 rounded-xl outline-none text-sm"
                    placeholder={$i18n.t('Search checklists')}
                    bind:value={searchQuery}
                />
            </div>
        </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-auto">
        {#if loading}
            <div class="flex justify-center items-center h-32">
                <Spinner />
            </div>
        {:else if filteredChecklists.length === 0}
            <div class="flex flex-col items-center justify-center h-full text-center">
                <div class="mb-3">
                    <svg
                        class="w-12 h-12 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </div>
                <div class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    {$i18n.t('No checklists found')}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400 mb-4">
                    {$i18n.t('Create your first checklist to get started')}
                </div>
                <a
                    href="/workspace/checklists/create"
                    class="px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-xl hover:bg-gray-800 dark:hover:bg-gray-200 transition"
                >
                    {$i18n.t('Create Checklist')}
                </a>
            </div>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {#each filteredChecklists as checklist}
                    <div class="bg-white dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800 p-4 hover:shadow-md transition-shadow">
                        <div class="flex items-start justify-between mb-3">
                            <div class="flex-1">
                                <div class="font-medium text-gray-900 dark:text-gray-100 mb-1">
                                    {checklist.title}
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400 font-mono">
                                    %{checklist.command}
                                </div>
                            </div>
                            
                            <div class="flex items-center space-x-1">
                                <a
                                    href="/workspace/checklists/edit?command={checklist.command}"
                                    class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                                    title={$i18n.t('Edit')}
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke-width="1.5"
                                        stroke="currentColor"
                                        class="w-4 h-4"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
                                        />
                                    </svg>
                                </a>
                                
                                <button
                                    on:click={() => deleteChecklist(checklist)}
                                    class="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition"
                                    title={$i18n.t('Delete')}
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke-width="1.5"
                                        stroke="currentColor"
                                        class="w-4 h-4"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                                        />
                                    </svg>
                                </button>
                            </div>
                        </div>
                        
                        {#if checklist.description}
                            <div class="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
                                {checklist.description}
                            </div>
                        {/if}
                        
                        <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                            <div class="flex items-center space-x-2">
                                <span>{checklist.items?.length || 0} prompts</span>
                                {#if checklist.user}
                                    <span>• by {checklist.user.name}</span>
                                {/if}
                            </div>
                            <div>
                                {new Date(checklist.timestamp * 1000).toLocaleDateString()}
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>