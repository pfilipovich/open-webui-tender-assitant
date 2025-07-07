<script>
    import { onMount } from 'svelte';
    import { checklists } from '$lib/stores';
    import { getChecklists } from '$lib/apis/checklists';
    import Checklists from '$lib/components/workspace/Checklists.svelte';

    onMount(async () => {
        checklists.set(await getChecklists(localStorage.token));
    });
</script>

{#if $checklists !== null}
    <Checklists />
{/if}
