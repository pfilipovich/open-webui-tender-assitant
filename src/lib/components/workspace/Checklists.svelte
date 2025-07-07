<script lang="ts">
    import { onMount, getContext } from 'svelte';
    import { checklists } from '$lib/stores';
    import { goto } from '$app/navigation';
    import { deleteChecklistById, getChecklistList, getChecklists } from '$lib/apis/checklists';
    import { toast } from 'svelte-sonner';
    import Plus from '$lib/components/icons/Plus.svelte';
    import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

    const i18n = getContext('i18n');

    let loaded = false;
    let list = [];
    let showDeleteConfirm = false;
    let deleteId = null;

    const init = async () => {
        list = await getChecklistList(localStorage.token);
    };

    const deleteHandler = async (id) => {
        await deleteChecklistById(localStorage.token, id);
        await init();
        checklists.set(await getChecklists(localStorage.token));
        toast.success(i18n.t('Deleted'));
    };

    onMount(async () => {
        await init();
        loaded = true;
    });
</script>

{#if loaded}
    <DeleteConfirmDialog bind:show={showDeleteConfirm} on:confirm={() => deleteHandler(deleteId)} />
    <div class="flex justify-between items-center my-2">
        <div class="text-xl font-medium">{i18n.t('Checklists')}</div>
        <button class="px-2 py-2 rounded-xl hover:bg-gray-700/10 dark:hover:bg-gray-100/10 transition" on:click={() => goto('/workspace/checklists/create')} aria-label={i18n.t('Create Checklist')}>
            <Plus className="size-3.5" />
        </button>
    </div>

    <div class="grid gap-2">
        {#each list as item}
            <div class="flex justify-between p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-850">
                <div class="font-medium">{item.title}</div>
                <div class="flex gap-1">
                    <button class="text-sm hover:underline" on:click={() => goto(`/workspace/checklists/create?id=${item.id}`)}>Edit</button>
                    <button class="text-sm hover:underline" on:click={() => { deleteId = item.id; showDeleteConfirm = true; }}>Delete</button>
                </div>
            </div>
        {/each}
    </div>
{:else}
    <div>Loading...</div>
{/if}
