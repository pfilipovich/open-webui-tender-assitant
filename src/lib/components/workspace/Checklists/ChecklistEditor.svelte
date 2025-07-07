<script lang="ts">
    import { onMount, getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import { createNewChecklist, updateChecklistById, getChecklistById } from '$lib/apis/checklists';
    import { goto } from '$app/navigation';
    import AccessControl from '../common/AccessControl.svelte';
    import { page } from '$app/stores';

    const i18n = getContext('i18n');

    export let id: string | null = null;

    let title = '';
    let items: { question: string }[] = [];
    let accessControl = {};
    let loading = false;

    const addItem = () => {
        items = [...items, { question: '' }];
    };

    const removeItem = (idx) => {
        items = items.filter((_, i) => i !== idx);
    };

    const submitHandler = async () => {
        loading = true;
        const form = { title, items, access_control: accessControl };
        let res = null;
        if (id) {
            res = await updateChecklistById(localStorage.token, id, form).catch((e) => {
                toast.error(`${e}`);
                return null;
            });
        } else {
            res = await createNewChecklist(localStorage.token, form).catch((e) => {
                toast.error(`${e}`);
                return null;
            });
        }

        if (res) {
            toast.success(i18n.t('Saved'));
            goto('/workspace/checklists');
        }
        loading = false;
    };

    onMount(async () => {
        const paramId = $page.url.searchParams.get('id');
        if (paramId) {
            id = paramId;
            const data = await getChecklistById(localStorage.token, id).catch(() => null);
            if (data) {
                title = data.title;
                items = data.items || [];
                accessControl = data.access_control || {};
            }
        } else {
            addItem();
        }
    });
</script>

<div class="space-y-2">
    <div>
        <input class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850" placeholder={i18n.t('Title')} bind:value={title} required />
    </div>

    <div class="space-y-2">
        {#each items as item, idx}
            <div class="flex gap-2">
                <input class="flex-1 rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850" placeholder={i18n.t('Question')} bind:value={item.question} required />
                <button type="button" on:click={() => removeItem(idx)} aria-label={i18n.t('Remove')}>×</button>
            </div>
        {/each}
        <button type="button" on:click={addItem}>{i18n.t('Add question')}</button>
    </div>

    <div class="px-3 py-2 bg-gray-50 dark:bg-gray-950 rounded-lg">
        <AccessControl bind:accessControl accessRoles={['read', 'write']} />
    </div>

    <div class="flex justify-end">
        <button class="px-4 py-2 rounded-lg bg-black text-white dark:bg-white dark:text-black" on:click={submitHandler} disabled={loading}>{i18n.t('Save')}</button>
    </div>
</div>
