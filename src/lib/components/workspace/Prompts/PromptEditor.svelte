<script lang="ts">
	import { onMount, tick, getContext } from 'svelte';

	import Textarea from '$lib/components/common/Textarea.svelte';
	import { toast } from 'svelte-sonner';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import AccessControl from '../common/AccessControl.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import AccessControlModal from '../common/AccessControlModal.svelte';
	import { user } from '$lib/stores';
	import { slugify } from '$lib/utils';

	export let onSubmit: Function;
	export let edit = false;
	export let prompt = null;
	export let clone = false;

	const i18n = getContext('i18n');

	let loading = false;

	let title = '';
	let command = '';
	let content = '';
	let structuredOutput = false;
	let structuredOutputSchema = '';
	let schemaError = '';

	let accessControl = {};

	let showAccessControlModal = false;

	let hasManualEdit = false;

	$: if (!edit && !hasManualEdit) {
		command = title !== '' ? slugify(title) : '';
	}

	// Track manual edits
	function handleCommandInput(e: Event) {
		hasManualEdit = true;
	}

	const submitHandler = async () => {
		loading = true;

		if (validateCommandString(command)) {
			// Validate schema if structured output is enabled
			if (structuredOutput && structuredOutputSchema.trim()) {
				if (!validateJsonSchema(structuredOutputSchema)) {
					loading = false;
					return;
				}
			}

			await onSubmit({
				title,
				command,
				content,
				access_control: accessControl,
				structured_output: structuredOutput,
				structured_output_schema: structuredOutput ? structuredOutputSchema || null : null
			});
		} else {
			toast.error(
				$i18n.t('Only alphanumeric characters and hyphens are allowed in the command string.')
			);
		}

		loading = false;
	};

	const validateCommandString = (inputString) => {
		// Regular expression to match only alphanumeric characters and hyphen
		const regex = /^[a-zA-Z0-9-]+$/;

		// Test the input string against the regular expression
		return regex.test(inputString);
	};

	const validateJsonSchema = (schemaStr) => {
		if (!schemaStr.trim()) {
			schemaError = '';
			return true;
		}

		try {
			const schema = JSON.parse(schemaStr);
			
			if (typeof schema !== 'object' || schema === null) {
				schemaError = $i18n.t('Schema must be a JSON object');
				return false;
			}
			
			if (!schema.type) {
				schemaError = $i18n.t('Schema must have a "type" field');
				return false;
			}
			
			schemaError = '';
			return true;
		} catch (e) {
			schemaError = $i18n.t('Invalid JSON format');
			return false;
		}
	};

	const insertSchemaExample = (exampleType) => {
		const examples = {
			simple: `{
  "type": "object",
  "properties": {
    "result": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  },
  "required": ["result"]
}`,
			checklist: `{
  "type": "object",
  "properties": {
    "task": {"type": "string"},
    "completed": {"type": "boolean"},
    "notes": {"type": "string"},
    "priority": {"type": "string", "enum": ["low", "medium", "high"]}
  },
  "required": ["task", "completed"]
}`,
			analysis: `{
  "type": "object",
  "properties": {
    "summary": {"type": "string"},
    "key_points": {
      "type": "array",
      "items": {"type": "string"}
    },
    "score": {"type": "integer", "minimum": 1, "maximum": 10}
  },
  "required": ["summary", "score"]
}`
		};
		structuredOutputSchema = examples[exampleType] || '';
		validateJsonSchema(structuredOutputSchema);
	};

	onMount(async () => {
		if (prompt) {
			title = prompt.title;
			await tick();

			command = prompt.command.at(0) === '/' ? prompt.command.slice(1) : prompt.command;
			content = prompt.content;
			structuredOutput = prompt.structured_output || false;
			structuredOutputSchema = prompt.structured_output_schema || '';

			accessControl = prompt?.access_control === undefined ? {} : prompt?.access_control;
		}
	});
</script>

<AccessControlModal
	bind:show={showAccessControlModal}
	bind:accessControl
	accessRoles={['read', 'write']}
	allowPublic={$user?.permissions?.sharing?.public_prompts || $user?.role === 'admin'}
/>

<div class="w-full max-h-full flex justify-center">
	<form
		class="flex flex-col w-full mb-10"
		on:submit|preventDefault={() => {
			submitHandler();
		}}
	>
		<div class="my-2">
			<Tooltip
				content={`${$i18n.t('Only alphanumeric characters and hyphens are allowed')} - ${$i18n.t(
					'Activate this command by typing "/{{COMMAND}}" to chat input.',
					{
						COMMAND: command
					}
				)}`}
				placement="bottom-start"
			>
				<div class="flex flex-col w-full">
					<div class="flex items-center">
						<input
							class="text-2xl font-semibold w-full bg-transparent outline-hidden"
							placeholder={$i18n.t('Title')}
							bind:value={title}
							required
						/>

						<div class="self-center shrink-0">
							<button
								class="bg-gray-50 hover:bg-gray-100 text-black dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white transition px-2 py-1 rounded-full flex gap-1 items-center"
								type="button"
								on:click={() => {
									showAccessControlModal = true;
								}}
							>
								<LockClosed strokeWidth="2.5" className="size-3.5" />

								<div class="text-sm font-medium shrink-0">
									{$i18n.t('Access')}
								</div>
							</button>
						</div>
					</div>

					<div class="flex gap-0.5 items-center text-xs text-gray-500">
						<div class="">/</div>
						<input
							class=" w-full bg-transparent outline-hidden"
							placeholder={$i18n.t('Command')}
							bind:value={command}
							on:input={handleCommandInput}
							required
							disabled={edit}
						/>
					</div>
				</div>
			</Tooltip>
		</div>

		<div class="my-2">
			<div class="flex w-full justify-between">
				<div class=" self-center text-sm font-semibold">{$i18n.t('Prompt Content')}</div>
			</div>

			<div class="mt-2">
				<div>
					<Textarea
						className="text-sm w-full bg-transparent outline-hidden overflow-y-hidden resize-none"
						placeholder={$i18n.t('Write a summary in 50 words that summarizes [topic or keyword].')}
						bind:value={content}
						rows={6}
						required
					/>
				</div>

				<div class="text-xs text-gray-400 dark:text-gray-500">
					ⓘ {$i18n.t('Format your variables using brackets like this:')}&nbsp;<span
						class=" text-gray-600 dark:text-gray-300 font-medium"
						>{'{{'}{$i18n.t('variable')}{'}}'}</span
					>.
					{$i18n.t('Make sure to enclose them with')}
					<span class=" text-gray-600 dark:text-gray-300 font-medium">{'{{'}</span>
					{$i18n.t('and')}
					<span class=" text-gray-600 dark:text-gray-300 font-medium">{'}}'}</span>.
				</div>

				<div class="text-xs text-gray-400 dark:text-gray-500">
					{$i18n.t('Utilize')}<span class=" text-gray-600 dark:text-gray-300 font-medium">
						{` {{CLIPBOARD}}`}</span
					>
					{$i18n.t('variable to have them replaced with clipboard content.')}
				</div>
			</div>
		</div>

		<div class="my-3">
			<div class="flex items-center gap-2">
				<input
					type="checkbox"
					id="structured-output"
					bind:checked={structuredOutput}
					class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
				/>
				<label for="structured-output" class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{$i18n.t('Return structured output as JSON (OpenAI models only)')}
				</label>
			</div>
			<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
				{$i18n.t('When enabled, the response will be formatted as JSON for easier parsing and processing')}
			</p>

			{#if structuredOutput}
				<div class="mt-4">
					<div class="flex w-full justify-between items-center mb-2">
						<div class="text-sm font-semibold">{$i18n.t('JSON Schema (Optional)')}</div>
						<div class="flex gap-1">
							<button
								type="button"
								class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition"
								on:click={() => insertSchemaExample('simple')}
							>
								{$i18n.t('Simple')}
							</button>
							<button
								type="button"
								class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition"
								on:click={() => insertSchemaExample('checklist')}
							>
								{$i18n.t('Checklist')}
							</button>
							<button
								type="button"
								class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded transition"
								on:click={() => insertSchemaExample('analysis')}
							>
								{$i18n.t('Analysis')}
							</button>
						</div>
					</div>

					<div>
						<Textarea
							className="text-sm w-full bg-transparent outline-hidden overflow-y-hidden resize-none font-mono {schemaError ? 'border-red-500' : ''}"
							placeholder={$i18n.t('Define JSON schema to validate AI responses (leave empty for basic JSON output)')}
							bind:value={structuredOutputSchema}
							on:input={() => validateJsonSchema(structuredOutputSchema)}
							rows={8}
						/>
					</div>

					{#if schemaError}
						<div class="text-xs text-red-500 mt-1">
							❌ {schemaError}
						</div>
					{:else if structuredOutputSchema.trim()}
						<div class="text-xs text-green-500 mt-1">
							✅ {$i18n.t('Valid JSON schema')}
						</div>
					{/if}

					<div class="text-xs text-gray-400 dark:text-gray-500 mt-2">
						ⓘ {$i18n.t('Define a JSON schema to ensure the AI response follows a specific structure. Leave empty to allow any JSON format.')}
					</div>
				</div>
			{/if}
		</div>

		<div class="my-4 flex justify-end pb-20">
			<button
				class=" text-sm w-full lg:w-fit px-4 py-2 transition rounded-lg {loading
					? ' cursor-not-allowed bg-black hover:bg-gray-900 text-white dark:bg-white dark:hover:bg-gray-100 dark:text-black'
					: 'bg-black hover:bg-gray-900 text-white dark:bg-white dark:hover:bg-gray-100 dark:text-black'} flex w-full justify-center"
				type="submit"
				disabled={loading}
			>
				<div class=" self-center font-medium">{$i18n.t('Save & Create')}</div>

				{#if loading}
					<div class="ml-1.5 self-center">
						<svg
							class=" w-4 h-4"
							viewBox="0 0 24 24"
							fill="currentColor"
							xmlns="http://www.w3.org/2000/svg"
							><style>
								.spinner_ajPY {
									transform-origin: center;
									animation: spinner_AtaB 0.75s infinite linear;
								}
								@keyframes spinner_AtaB {
									100% {
										transform: rotate(360deg);
									}
								}
							</style><path
								d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z"
								opacity=".25"
							/><path
								d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"
								class="spinner_ajPY"
							/></svg
						>
					</div>
				{/if}
			</button>
		</div>
	</form>
</div>
