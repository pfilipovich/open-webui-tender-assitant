<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, checklists as _checklists, user } from '$lib/stores';
	const i18n = getContext('i18n');

	import {
		getChecklistList,
		deleteChecklistByCommand
	} from '$lib/apis/checklists';
	import type { ChecklistUserResponse } from '$lib/apis/checklists';

	import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Search from '../icons/Search.svelte';
	import Plus from '../icons/Plus.svelte';
	import Spinner from '../common/Spinner.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import XMark from '../icons/XMark.svelte';

	let loaded = false;
	let query = '';
	let checklists: ChecklistUserResponse[] = [];
	let showDeleteConfirm = false;
	let deleteChecklistItem = null;

	let filteredItems = [];
	$: filteredItems = checklists.filter((c) => {
		if (query === '') return true;
		const lowerQuery = query.toLowerCase();
		return (
			(c.title || '').toLowerCase().includes(lowerQuery) ||
			(c.command || '').toLowerCase().includes(lowerQuery) ||
			(c.description || '').toLowerCase().includes(lowerQuery) ||
			(c.user?.name || '').toLowerCase().includes(lowerQuery) ||
			(c.user?.email || '').toLowerCase().includes(lowerQuery)
		);
	});

	const deleteHandler = async (checklist) => {
		const command = checklist.command;
		await deleteChecklistByCommand(localStorage.token, command);
		await init();
	};

	const init = async () => {
		checklists = await getChecklistList(localStorage.token);
		await _checklists.set(checklists);
	};

	onMount(async () => {
		await init();
		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Checklists')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<DeleteConfirmDialog
		bind:show={showDeleteConfirm}
		title={$i18n.t('Delete checklist?')}
		on:confirm={() => {
			deleteHandler(deleteChecklistItem);
		}}
	>
		<div class=" text-sm text-gray-500">
			{$i18n.t('This will delete')} <span class="  font-semibold">{deleteChecklistItem?.command}</span>.
		</div>
	</DeleteConfirmDialog>

	<div class="flex flex-col gap-1 my-1.5">
		<div class="flex justify-between items-center">
			<div class="flex md:self-center text-xl font-medium px-0.5 items-center">
				{$i18n.t('Checklists')}
				<div class="flex self-center w-[1px] h-6 mx-2.5 bg-gray-50 dark:bg-gray-850" />
				<span class="text-lg font-medium text-gray-500 dark:text-gray-300"
					>{filteredItems.length}</span
				>
			</div>
		</div>

		<div class=" flex w-full space-x-2">
			<div class="flex flex-1">
				<div class=" self-center ml-1 mr-3">
					<Search className="size-3.5" />
				</div>
				<input
					class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={query}
					placeholder={$i18n.t('Search Checklists')}
				/>

				{#if query}
					<div class="self-center pl-1.5 translate-y-[0.5px] rounded-l-xl bg-transparent">
						<button
							class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-900 transition"
							on:click={() => {
								query = '';
							}}
						>
							<XMark className="size-3" strokeWidth="2" />
						</button>
					</div>
				{/if}
			</div>

			<div>
				<a
					class=" px-2 py-2 rounded-xl hover:bg-gray-700/10 dark:hover:bg-gray-100/10 dark:text-gray-300 dark:hover:text-white transition font-medium text-sm flex items-center space-x-1"
					href="/workspace/checklists/create"
				>
					<Plus className="size-3.5" />
				</a>
			</div>
		</div>
	</div>

	<div class="mb-5 gap-2 grid lg:grid-cols-2 xl:grid-cols-3">
		{#each filteredItems as checklist}
			<div
				class=" flex space-x-4 cursor-pointer w-full px-3 py-2 dark:hover:bg-white/5 hover:bg-black/5 rounded-xl transition"
			>
				<div class=" flex flex-1 space-x-4 cursor-pointer w-full">
					<a href={`/workspace/checklists/edit?command=${encodeURIComponent(checklist.command)}`}>
						<div class=" flex-1 flex items-center gap-2 self-center">
							<div class=" font-semibold line-clamp-1 capitalize">{checklist.title}</div>
							<div class=" text-xs overflow-hidden text-ellipsis line-clamp-1">
								%{checklist.command}
							</div>
						</div>

						<div class=" text-xs px-0.5">
							<Tooltip
								content={checklist?.user?.email ?? $i18n.t('Deleted User')}
								className="flex shrink-0"
								placement="top-start"
							>
								<div class="shrink-0 text-gray-500">
									{$i18n.t('By {{name}}', {
										name: checklist?.user?.name ?? checklist?.user?.email ?? $i18n.t('Deleted User')
									})}
								</div>
							</Tooltip>
						</div>
					</a>
				</div>
				<div class="flex flex-row gap-0.5 self-center">
					<a
						class="self-center w-fit text-sm px-2 py-2 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
						type="button"
						href={`/workspace/checklists/edit?command=${encodeURIComponent(checklist.command)}`}
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
								d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
							/>
						</svg>
					</a>

					<button
						class="self-center w-fit text-sm p-1.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
						type="button"
						on:click={() => {
							deleteChecklistItem = checklist;
							showDeleteConfirm = true;
						}}
					>
						<EllipsisHorizontal className="size-5" />
					</button>
				</div>
			</div>
		{/each}
	</div>

	{#if filteredItems.length === 0}
		<div class="flex flex-col items-center justify-center h-full text-center py-16">
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
	{/if}
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner />
	</div>
{/if}