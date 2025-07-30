<script lang="ts">
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';

	import { toast } from 'svelte-sonner';

	import { v4 as uuidv4 } from 'uuid';
	import { createPicker, getAuthToken } from '$lib/utils/google-drive-picker';
	import { pickAndDownloadFile } from '$lib/utils/onedrive-file-picker';

	import { onMount, tick, getContext, createEventDispatcher, onDestroy } from 'svelte';
	const dispatch = createEventDispatcher();

	import {
		type Model,
		mobile,
		settings,
		showSidebar,
		models,
		config,
		showCallOverlay,
		tools,
		user as _user,
		showControls,
		TTSWorker
	} from '$lib/stores';

	import {
		blobToFile,
		compressImage,
		createMessagesList,
		extractCurlyBraceWords
	} from '$lib/utils';
	import { uploadFile } from '$lib/apis/files';
	import { generateAutoCompletion } from '$lib/apis';
	import { deleteFileById } from '$lib/apis/files';

	import { WEBUI_BASE_URL, WEBUI_API_BASE_URL, PASTED_TEXT_CHARACTER_LIMIT } from '$lib/constants';

	import InputMenu from './MessageInput/InputMenu.svelte';
	import VoiceRecording from './MessageInput/VoiceRecording.svelte';
	import FilesOverlay from './MessageInput/FilesOverlay.svelte';
	import Commands from './MessageInput/Commands.svelte';
	import ToolServersModal from './ToolServersModal.svelte';

	import RichTextInput from '../common/RichTextInput.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import FileItem from '../common/FileItem.svelte';
	import Image from '../common/Image.svelte';

	import XMark from '../icons/XMark.svelte';
	import Headphone from '../icons/Headphone.svelte';
	import GlobeAlt from '../icons/GlobeAlt.svelte';
	import Photo from '../icons/Photo.svelte';
	import Wrench from '../icons/Wrench.svelte';
	import CommandLine from '../icons/CommandLine.svelte';
	import Sparkles from '../icons/Sparkles.svelte';

	import { KokoroWorker } from '$lib/workers/KokoroWorker';

	const i18n = getContext('i18n');

	export let transparentBackground = false;

	export let onChange: Function = () => {};
	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;

	export let atSelectedModel: Model | undefined = undefined;
	export let selectedModels: [''];

	let selectedModelIds = [];
	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;

	export let history;
	export let taskIds = null;

	export let prompt = '';
	export let files = [];

	export let toolServers = [];

	export let selectedToolIds = [];
	export let selectedFilterIds = [];

	// External structured output from Chat.svelte (for prompt commands)
	export let externalStructuredOutput = false;
	export let externalStructuredOutputSchema = '';
	export let externalStructuredOutputName = '';

	let currentPromptStructuredOutput = false;
	let structuredOutputSchema = '';
	let structuredOutputName = '';
	let structuredOutputEnabled = false;
	
	// Prompt attachment state
	let attachedPrompt = null;

	// Computed values for display - combines UI, external, and attached prompt structured output
	$: attachedPromptStructuredOutput = attachedPrompt?.structured_output || false;
	$: attachedPromptStructuredOutputSchema = attachedPrompt?.structured_output_schema || '';
	$: attachedPromptName = attachedPrompt?.title || attachedPrompt?.name || '';
	
	$: displayStructuredOutput = structuredOutputEnabled || externalStructuredOutput || attachedPromptStructuredOutput;
	$: displayStructuredOutputSchema = structuredOutputSchema || externalStructuredOutputSchema || attachedPromptStructuredOutputSchema;
	$: displayStructuredOutputName = structuredOutputName || externalStructuredOutputName || (attachedPromptStructuredOutput ? attachedPromptName : '');
	
	// Debug logging for state changes
	$: {
		console.log('🔄 MessageInput state update:', {
			structuredOutputEnabled,
			externalStructuredOutput,
			displayStructuredOutput,
			structuredOutputSchema: structuredOutputSchema?.length || 0,
			externalStructuredOutputSchema: externalStructuredOutputSchema?.length || 0,
			displayStructuredOutputSchema: displayStructuredOutputSchema?.length || 0
		});
	}

	// Reset structured output flag when prompt changes (unless from command)
	$: if (prompt && !prompt.startsWith('/')) {
		currentPromptStructuredOutput = false;
		// CRITICAL: Don't reset manual UI configuration when prompt changes!
		// structuredOutputEnabled should persist until manually cleared
		console.log('🔄 Prompt changed (non-command), keeping manual structured output config:', {
			prompt: prompt.substring(0, 50) + '...',
			structuredOutputEnabled,
			'Will NOT reset': 'Manual UI configuration persists'
		});
	}

	export let imageGenerationEnabled = false;
	export let webSearchEnabled = false;
	export let codeInterpreterEnabled = false;

	$: {
		// Calculate structured output values directly instead of relying on computed properties
		// to avoid reactive timing issues
		const currentStructuredOutput = structuredOutputEnabled || externalStructuredOutput || (attachedPrompt?.structured_output || false);
		const currentStructuredOutputSchema = structuredOutputSchema || externalStructuredOutputSchema || (attachedPrompt?.structured_output_schema || '');
		const currentStructuredOutputName = structuredOutputName || externalStructuredOutputName || (attachedPrompt?.structured_output && (attachedPrompt?.title || attachedPrompt?.name) ? (attachedPrompt.title || attachedPrompt.name) : '');
		
		const structuredOutputData = {
			structuredOutput: currentStructuredOutput,
			structuredOutputSchema: currentStructuredOutputSchema,
			structuredOutputName: currentStructuredOutputName
		};
		
		// ULTRA-DEBUG: Log every reactive update to catch state resets
		console.log('🔄 MessageInput REACTIVE UPDATE triggered:', {
			trigger: 'reactive_block',
			timestamp: new Date().toISOString(),
			prompt: prompt?.substring(0, 50) + (prompt?.length > 50 ? '...' : ''),
			structuredOutputEnabled,
			externalStructuredOutput,
			attachedPromptSO: attachedPrompt?.structured_output || false,
			finalStructuredOutput: structuredOutputData.structuredOutput,
			finalSchemaLength: structuredOutputData.structuredOutputSchema?.length || 0,
			stackTrace: new Error().stack?.split('\n')[1] || 'unknown'
		});
		
		// Enhanced logging for structured output state
		if (structuredOutputData.structuredOutput) {
			console.log('📤 MessageInput sending structured output:', {
				...structuredOutputData,
				schemaLength: structuredOutputData.structuredOutputSchema?.length || 0,
				source: structuredOutputEnabled ? 'manual_ui' : attachedPrompt?.structured_output ? 'attached_prompt' : 'external_prompt'
			});
		} else if (externalStructuredOutput || structuredOutputEnabled || attachedPrompt?.structured_output) {
			console.log('📤 MessageInput structured output debug:', {
				structuredOutputEnabled,
				externalStructuredOutput,
				attachedPromptSO: attachedPrompt?.structured_output || false,
				currentStructuredOutput,
				'Diagnosis': 'Flags are set but final output is false - check reactive dependencies'
			});
		}
		
		// Defensive check to ensure onChange is available before calling
		if (onChange) {
			onChange({
				prompt,
				files: files
					.filter((file) => file.type !== 'image')
					.map((file) => {
						return {
							...file,
							user: undefined,
							access_control: undefined
						};
					}),
				...structuredOutputData,
				attachedPrompt,
				selectedToolIds,
				selectedFilterIds,
				imageGenerationEnabled,
				webSearchEnabled,
				codeInterpreterEnabled
			});
		} else {
			console.warn('📤 MessageInput onChange not available, structured output data not sent:', {
				hasStructuredOutput: structuredOutputData.structuredOutput,
				schemaLength: structuredOutputData.structuredOutputSchema?.length || 0
			});
		}
	}

	// Ensure initial structured output state is properly sent to parent on mount
	onMount(() => {
		// Small delay to ensure parent is ready to receive onChange calls
		setTimeout(() => {
			const initialStructuredOutput = structuredOutputEnabled || externalStructuredOutput || (attachedPrompt?.structured_output || false);
			const initialStructuredOutputSchema = structuredOutputSchema || externalStructuredOutputSchema || (attachedPrompt?.structured_output_schema || '');
			const initialStructuredOutputName = structuredOutputName || externalStructuredOutputName || (attachedPrompt?.structured_output && (attachedPrompt?.title || attachedPrompt?.name) ? (attachedPrompt.title || attachedPrompt.name) : '');
			
			if (initialStructuredOutput && onChange) {
				console.log('🚀 MOUNT: Sending initial structured output state to parent:', {
					structuredOutput: initialStructuredOutput,
					schemaLength: initialStructuredOutputSchema?.length || 0,
					name: initialStructuredOutputName
				});
				
				onChange({
					prompt,
					files: files
						.filter((file) => file.type !== 'image')
						.map((file) => {
							return {
								...file,
								user: undefined,
								access_control: undefined
							};
						}),
					structuredOutput: initialStructuredOutput,
					structuredOutputSchema: initialStructuredOutputSchema,
					structuredOutputName: initialStructuredOutputName,
					attachedPrompt,
					selectedToolIds,
					selectedFilterIds,
					imageGenerationEnabled,
					webSearchEnabled,
					codeInterpreterEnabled
				});
			}
		}, 10); // Small delay to ensure parent binding is ready
	});

	let showTools = false;

	let loaded = false;
	let recording = false;

	let isComposing = false;

	let chatInputContainerElement;
	let chatInputElement;

	let filesInputElement;
	let commandsElement;

	let inputFiles;

	let dragged = false;
	let shiftKey = false;

	let user = null;
	export let placeholder = '';

	let visionCapableModels = [];
	$: visionCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.vision ?? true
	);

	let fileUploadCapableModels = [];
	$: fileUploadCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.file_upload ?? true
	);

	let webSearchCapableModels = [];
	$: webSearchCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.web_search ?? true
	);

	let imageGenerationCapableModels = [];
	$: imageGenerationCapableModels = (
		atSelectedModel?.id ? [atSelectedModel.id] : selectedModels
	).filter(
		(model) =>
			$models.find((m) => m.id === model)?.info?.meta?.capabilities?.image_generation ?? true
	);

	let codeInterpreterCapableModels = [];
	$: codeInterpreterCapableModels = (
		atSelectedModel?.id ? [atSelectedModel.id] : selectedModels
	).filter(
		(model) =>
			$models.find((m) => m.id === model)?.info?.meta?.capabilities?.code_interpreter ?? true
	);

	let toggleFilters = [];
	$: toggleFilters = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels)
		.map((id) => ($models.find((model) => model.id === id) || {})?.filters ?? [])
		.reduce((acc, filters) => acc.filter((f1) => filters.some((f2) => f2.id === f1.id)));

	let showToolsButton = false;
	$: showToolsButton = toolServers.length + selectedToolIds.length > 0;

	let showWebSearchButton = false;
	$: showWebSearchButton =
		(atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).length ===
			webSearchCapableModels.length &&
		$config?.features?.enable_web_search &&
		($_user.role === 'admin' || $_user?.permissions?.features?.web_search);

	let showImageGenerationButton = false;
	$: showImageGenerationButton =
		(atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).length ===
			imageGenerationCapableModels.length &&
		$config?.features?.enable_image_generation &&
		($_user.role === 'admin' || $_user?.permissions?.features?.image_generation);

	let showCodeInterpreterButton = false;
	$: showCodeInterpreterButton =
		(atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).length ===
			codeInterpreterCapableModels.length &&
		$config?.features?.enable_code_interpreter &&
		($_user.role === 'admin' || $_user?.permissions?.features?.code_interpreter);

	let showStructuredOutputButton = true;
	// Always show structured output button for better discoverability
	$: showStructuredOutputButton = true;

	const scrollToBottom = () => {
		const element = document.getElementById('messages-container');
		element.scrollTo({
			top: element.scrollHeight,
			behavior: 'smooth'
		});
	};

	const screenCaptureHandler = async () => {
		try {
			// Request screen media
			const mediaStream = await navigator.mediaDevices.getDisplayMedia({
				video: { cursor: 'never' },
				audio: false
			});
			// Once the user selects a screen, temporarily create a video element
			const video = document.createElement('video');
			video.srcObject = mediaStream;
			// Ensure the video loads without affecting user experience or tab switching
			await video.play();
			// Set up the canvas to match the video dimensions
			const canvas = document.createElement('canvas');
			canvas.width = video.videoWidth;
			canvas.height = video.videoHeight;
			// Grab a single frame from the video stream using the canvas
			const context = canvas.getContext('2d');
			context.drawImage(video, 0, 0, canvas.width, canvas.height);
			// Stop all video tracks (stop screen sharing) after capturing the image
			mediaStream.getTracks().forEach((track) => track.stop());

			// bring back focus to this current tab, so that the user can see the screen capture
			window.focus();

			// Convert the canvas to a Base64 image URL
			const imageUrl = canvas.toDataURL('image/png');
			// Add the captured image to the files array to render it
			files = [...files, { type: 'image', url: imageUrl }];
			// Clean memory: Clear video srcObject
			video.srcObject = null;
		} catch (error) {
			// Handle any errors (e.g., user cancels screen sharing)
			console.error('Error capturing screen:', error);
		}
	};

	const uploadFileHandler = async (file, fullContext: boolean = false) => {
		if ($_user?.role !== 'admin' && !($_user?.permissions?.chat?.file_upload ?? true)) {
			toast.error($i18n.t('You do not have permission to upload files.'));
			return null;
		}

		const tempItemId = uuidv4();
		const fileItem = {
			type: 'file',
			file: '',
			id: null,
			url: '',
			name: file.name,
			collection_name: '',
			status: 'uploading',
			size: file.size,
			error: '',
			itemId: tempItemId,
			...(fullContext ? { context: 'full' } : {})
		};

		if (fileItem.size == 0) {
			toast.error($i18n.t('You cannot upload an empty file.'));
			return null;
		}

		files = [...files, fileItem];

		try {
			// If the file is an audio file, provide the language for STT.
			let metadata = null;
			if (
				(file.type.startsWith('audio/') || file.type.startsWith('video/')) &&
				$settings?.audio?.stt?.language
			) {
				metadata = {
					language: $settings?.audio?.stt?.language
				};
			}

			// During the file upload, file content is automatically extracted.
			const uploadedFile = await uploadFile(localStorage.token, file, metadata);

			if (uploadedFile) {
				console.log('File upload completed:', {
					id: uploadedFile.id,
					name: fileItem.name,
					collection: uploadedFile?.meta?.collection_name
				});

				if (uploadedFile.error) {
					console.warn('File upload warning:', uploadedFile.error);
					toast.warning(uploadedFile.error);
				}

				fileItem.status = 'uploaded';
				fileItem.file = uploadedFile;
				fileItem.id = uploadedFile.id;
				fileItem.collection_name =
					uploadedFile?.meta?.collection_name || uploadedFile?.collection_name;
				fileItem.url = `${WEBUI_API_BASE_URL}/files/${uploadedFile.id}`;

				files = files;
			} else {
				files = files.filter((item) => item?.itemId !== tempItemId);
			}
		} catch (e) {
			toast.error(`${e}`);
			files = files.filter((item) => item?.itemId !== tempItemId);
		}
	};

	const inputFilesHandler = async (inputFiles) => {
		console.log('Input files handler called with:', inputFiles);

		if (
			($config?.file?.max_count ?? null) !== null &&
			files.length + inputFiles.length > $config?.file?.max_count
		) {
			toast.error(
				$i18n.t(`You can only chat with a maximum of {{maxCount}} file(s) at a time.`, {
					maxCount: $config?.file?.max_count
				})
			);
			return;
		}

		inputFiles.forEach((file) => {
			console.log('Processing file:', {
				name: file.name,
				type: file.type,
				size: file.size,
				extension: file.name.split('.').at(-1)
			});

			if (
				($config?.file?.max_size ?? null) !== null &&
				file.size > ($config?.file?.max_size ?? 0) * 1024 * 1024
			) {
				console.log('File exceeds max size limit:', {
					fileSize: file.size,
					maxSize: ($config?.file?.max_size ?? 0) * 1024 * 1024
				});
				toast.error(
					$i18n.t(`File size should not exceed {{maxSize}} MB.`, {
						maxSize: $config?.file?.max_size
					})
				);
				return;
			}

			if (
				['image/gif', 'image/webp', 'image/jpeg', 'image/png', 'image/avif'].includes(file['type'])
			) {
				if (visionCapableModels.length === 0) {
					toast.error($i18n.t('Selected model(s) do not support image inputs'));
					return;
				}
				let reader = new FileReader();
				reader.onload = async (event) => {
					let imageUrl = event.target.result;

					if (
						($settings?.imageCompression ?? false) ||
						($config?.file?.image_compression?.width ?? null) ||
						($config?.file?.image_compression?.height ?? null)
					) {
						let width = null;
						let height = null;

						if ($settings?.imageCompression ?? false) {
							width = $settings?.imageCompressionSize?.width ?? null;
							height = $settings?.imageCompressionSize?.height ?? null;
						}

						if (
							($config?.file?.image_compression?.width ?? null) ||
							($config?.file?.image_compression?.height ?? null)
						) {
							if (width > ($config?.file?.image_compression?.width ?? null)) {
								width = $config?.file?.image_compression?.width ?? null;
							}
							if (height > ($config?.file?.image_compression?.height ?? null)) {
								height = $config?.file?.image_compression?.height ?? null;
							}
						}

						if (width || height) {
							imageUrl = await compressImage(imageUrl, width, height);
						}
					}

					files = [
						...files,
						{
							type: 'image',
							url: `${imageUrl}`
						}
					];
				};
				reader.readAsDataURL(file);
			} else {
				uploadFileHandler(file);
			}
		});
	};

	const onDragOver = (e) => {
		e.preventDefault();

		// Check if a file is being dragged.
		if (e.dataTransfer?.types?.includes('Files')) {
			dragged = true;
		} else {
			dragged = false;
		}
	};

	const onDragLeave = () => {
		dragged = false;
	};

	const onDrop = async (e) => {
		e.preventDefault();
		console.log(e);

		if (e.dataTransfer?.files) {
			const inputFiles = Array.from(e.dataTransfer?.files);
			if (inputFiles && inputFiles.length > 0) {
				console.log(inputFiles);
				inputFilesHandler(inputFiles);
			}
		}

		dragged = false;
	};

	const onKeyDown = (e) => {
		if (e.key === 'Shift') {
			shiftKey = true;
		}

		if (e.key === 'Escape') {
			console.log('Escape');
			dragged = false;
		}
	};

	const onKeyUp = (e) => {
		if (e.key === 'Shift') {
			shiftKey = false;
		}
	};

	const onFocus = () => {};

	const onBlur = () => {
		shiftKey = false;
	};

	onMount(async () => {
		loaded = true;

		window.setTimeout(() => {
			const chatInput = document.getElementById('chat-input');
			chatInput?.focus();
		}, 0);

		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);

		window.addEventListener('focus', onFocus);
		window.addEventListener('blur', onBlur);

		await tick();

		const dropzoneElement = document.getElementById('chat-container');

		dropzoneElement?.addEventListener('dragover', onDragOver);
		dropzoneElement?.addEventListener('drop', onDrop);
		dropzoneElement?.addEventListener('dragleave', onDragLeave);
	});

	onDestroy(() => {
		console.log('destroy');
		window.removeEventListener('keydown', onKeyDown);
		window.removeEventListener('keyup', onKeyUp);

		window.removeEventListener('focus', onFocus);
		window.removeEventListener('blur', onBlur);

		const dropzoneElement = document.getElementById('chat-container');

		if (dropzoneElement) {
			dropzoneElement?.removeEventListener('dragover', onDragOver);
			dropzoneElement?.removeEventListener('drop', onDrop);
			dropzoneElement?.removeEventListener('dragleave', onDragLeave);
		}
	});
</script>

<FilesOverlay show={dragged} />
<ToolServersModal bind:show={showTools} {selectedToolIds} />

{#if loaded}
	<div class="w-full font-primary">
		<div class=" mx-auto inset-x-0 bg-transparent flex justify-center">
			<div
				class="flex flex-col px-3 {($settings?.widescreenMode ?? null)
					? 'max-w-full'
					: 'max-w-6xl'} w-full"
			>
				<div class="relative">
					{#if autoScroll === false && history?.currentId}
						<div
							class=" absolute -top-12 left-0 right-0 flex justify-center z-30 pointer-events-none"
						>
							<button
								class=" bg-white border border-gray-100 dark:border-none dark:bg-white/20 p-1.5 rounded-full pointer-events-auto"
								on:click={() => {
									autoScroll = true;
									scrollToBottom();
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-5 h-5"
								>
									<path
										fill-rule="evenodd"
										d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>
						</div>
					{/if}
				</div>

				<div class="w-full relative">
					{#if atSelectedModel !== undefined}
						<div
							class="px-3 pb-0.5 pt-1.5 text-left w-full flex flex-col absolute bottom-0 left-0 right-0 bg-linear-to-t from-white dark:from-gray-900 z-10"
						>
							<div class="flex items-center justify-between w-full">
								<div class="pl-[1px] flex items-center gap-2 text-sm dark:text-gray-500">
									<img
										crossorigin="anonymous"
										alt="model profile"
										class="size-3.5 max-w-[28px] object-cover rounded-full"
										src={$models.find((model) => model.id === atSelectedModel.id)?.info?.meta
											?.profile_image_url ??
											($i18n.language === 'dg-DG'
												? `/doge.png`
												: `${WEBUI_BASE_URL}/static/favicon.png`)}
									/>
									<div class="translate-y-[0.5px]">
										Talking to <span class=" font-medium">{atSelectedModel.name}</span>
									</div>
								</div>
								<div>
									<button
										class="flex items-center dark:text-gray-500"
										on:click={() => {
											atSelectedModel = undefined;
										}}
									>
										<XMark />
									</button>
								</div>
							</div>
						</div>
					{/if}

					<Commands
						bind:this={commandsElement}
						bind:prompt
						bind:files
						on:upload={(e) => {
							dispatch('upload', e.detail);
						}}
						on:select={(e) => {
							const data = e.detail;

							if (data?.type === 'model') {
								atSelectedModel = data.data;
							}

							const chatInputElement = document.getElementById('chat-input');
							chatInputElement?.focus();
						}}
						on:structuredOutput={(e) => {
							currentPromptStructuredOutput = e.detail.structured_output;
						}}
					/>
				</div>
			</div>
		</div>

		<div class="{transparentBackground ? 'bg-transparent' : 'bg-white dark:bg-gray-900'} ">
			<div
				class="{($settings?.widescreenMode ?? null)
					? 'max-w-full'
					: 'max-w-6xl'} px-2.5 mx-auto inset-x-0"
			>
				<div class="">
					<input
						bind:this={filesInputElement}
						bind:files={inputFiles}
						type="file"
						hidden
						multiple
						on:change={async () => {
							if (inputFiles && inputFiles.length > 0) {
								const _inputFiles = Array.from(inputFiles);
								inputFilesHandler(_inputFiles);
							} else {
								toast.error($i18n.t(`File not found.`));
							}

							filesInputElement.value = '';
						}}
					/>

					{#if recording}
						<VoiceRecording
							bind:recording
							onCancel={async () => {
								recording = false;

								await tick();
								document.getElementById('chat-input')?.focus();
							}}
							onConfirm={async (data) => {
								const { text, filename } = data;
								prompt = `${prompt}${text} `;

								recording = false;

								await tick();
								document.getElementById('chat-input')?.focus();

								if ($settings?.speechAutoSend ?? false) {
									dispatch('submit', prompt);
								}
							}}
						/>
					{:else}
						<form
							class="w-full flex flex-col gap-1.5"
							on:submit|preventDefault={() => {
								// check if selectedModels support image input
								dispatch('submit', prompt);
							}}
						>
							<div
								class="flex-1 flex flex-col relative w-full shadow-lg rounded-3xl border border-gray-50 dark:border-gray-850 hover:border-gray-100 focus-within:border-gray-100 hover:dark:border-gray-800 focus-within:dark:border-gray-800 transition px-1 bg-white/90 dark:bg-gray-400/5 dark:text-gray-100"
								dir={$settings?.chatDirection ?? 'auto'}
							>
								{#if files.length > 0}
									<div class="mx-2 mt-2.5 -mb-1 flex items-center flex-wrap gap-2">
										{#each files as file, fileIdx}
											{#if file.type === 'image'}
												<div class=" relative group">
													<div class="relative flex items-center">
														<Image
															src={file.url}
															alt="input"
															imageClassName=" size-14 rounded-xl object-cover"
														/>
														{#if atSelectedModel ? visionCapableModels.length === 0 : selectedModels.length !== visionCapableModels.length}
															<Tooltip
																className=" absolute top-1 left-1"
																content={$i18n.t('{{ models }}', {
																	models: [
																		...(atSelectedModel ? [atSelectedModel] : selectedModels)
																	]
																		.filter((id) => !visionCapableModels.includes(id))
																		.join(', ')
																})}
															>
																<svg
																	xmlns="http://www.w3.org/2000/svg"
																	viewBox="0 0 24 24"
																	fill="currentColor"
																	class="size-4 fill-yellow-300"
																>
																	<path
																		fill-rule="evenodd"
																		d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003ZM12 8.25a.75.75 0 0 1 .75.75v3.75a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75Zm0 8.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
																		clip-rule="evenodd"
																	/>
																</svg>
															</Tooltip>
														{/if}
													</div>
													<div class=" absolute -top-1 -right-1">
														<button
															class=" bg-white text-black border border-white rounded-full group-hover:visible invisible transition"
															type="button"
															on:click={() => {
																files.splice(fileIdx, 1);
																files = files;
															}}
														>
															<svg
																xmlns="http://www.w3.org/2000/svg"
																viewBox="0 0 20 20"
																fill="currentColor"
																class="size-4"
															>
																<path
																	d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
																/>
															</svg>
														</button>
													</div>
												</div>
											{:else}
												<FileItem
													item={file}
													name={file.name}
													type={file.type}
													size={file?.size}
													loading={file.status === 'uploading'}
													dismissible={true}
													edit={true}
													on:dismiss={async () => {
														try {
															if (file.type !== 'collection' && !file?.collection) {
																if (file.id) {
																	// This will handle both file deletion and Chroma cleanup
																	await deleteFileById(localStorage.token, file.id);
																}
															}
														} catch (error) {
															console.error('Error deleting file:', error);
														}

														// Remove from UI state
														files.splice(fileIdx, 1);
														files = files;
													}}
													on:click={() => {
														console.log(file);
													}}
												/>
											{/if}
										{/each}
									</div>
								{/if}

								{#if attachedPrompt}
									<div class="mx-2 mt-2.5 -mb-1 flex items-center">
										<div class="flex items-center gap-2 px-3 py-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
											<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-purple-600 dark:text-purple-400">
												<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3-9.75H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25H6A2.25 2.25 0 013.75 18V6A2.25 2.25 0 016 3.75h4.125C11.25 3.75 12 4.5 12 5.25v1.5h3V18z"/>
											</svg>
											<span class="text-sm text-purple-700 dark:text-purple-300 font-medium">
												{attachedPrompt.title || attachedPrompt.name || 'Prompt'}
											</span>
											{#if attachedPromptStructuredOutput}
												<div class="flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-800/30 rounded text-xs text-blue-700 dark:text-blue-300">
													<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
														<path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
													</svg>
													SO
												</div>
											{/if}
											<button 
												on:click={() => {
													attachedPrompt = null;
												}}
												class="text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-200 transition"
												title={$i18n.t('Remove prompt')}
											>
												<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
													<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
												</svg>
											</button>
										</div>
									</div>
								{/if}

								{#if displayStructuredOutput && displayStructuredOutputSchema && !attachedPromptStructuredOutput}
									<div class="mx-2 mt-2.5 -mb-1 flex items-center">
										<div class="flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
											<div class="flex items-center gap-2">
												<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-blue-600 dark:text-blue-400">
													<path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
												</svg>
												<span class="text-sm text-blue-700 dark:text-blue-300 font-medium">
													{displayStructuredOutputName || 'Structured Output'}
												</span>
												{#if externalStructuredOutput}
													<span class="text-xs text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-800/30 px-1.5 py-0.5 rounded" title="From external command">
														⌘
													</span>
												{:else}
													<span class="text-xs text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-800/30 px-1.5 py-0.5 rounded" title="Manual configuration">
														✓
													</span>
												{/if}
											</div>
											{#if !externalStructuredOutput}
												<button 
													on:click={() => {
														// Find the InputMenu component and trigger the structured output modal
														const moreBtn = document.querySelector('[aria-label="More"]');
														if (moreBtn) {
															moreBtn.click();
															// Small delay to let the dropdown open, then click structured output
															setTimeout(() => {
																const structuredOutputBtn = document.querySelector('[data-structured-output-btn]');
																if (structuredOutputBtn) {
																	structuredOutputBtn.click();
																}
															}, 50);
														}
													}}
													class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 transition"
													title={$i18n.t('Edit structured output')}
												>
													<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
														<path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
													</svg>
												</button>
											{:else}
												<span 
													class="text-gray-400 dark:text-gray-500 cursor-not-allowed"
													title="Cannot edit prompt-based structured output"
												>
													<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
														<path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
													</svg>
												</span>
											{/if}
											{#if !externalStructuredOutput}
												<button 
													on:click={() => {
														structuredOutputSchema = '';
														structuredOutputName = '';
														structuredOutputEnabled = false;
														currentPromptStructuredOutput = false;
													}}
													class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200 transition"
													title={$i18n.t('Remove structured output')}
												>
													<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
														<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
													</svg>
												</button>
											{:else}
												<span 
													class="text-gray-400 dark:text-gray-500 cursor-not-allowed"
													title="Structured output from prompt command"
												>
													<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
														<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
													</svg>
												</span>
											{/if}
										</div>
									</div>
								{/if}

								<div class="px-2.5">
									{#if $settings?.richTextInput ?? true}
										<div
											class="scrollbar-hidden rtl:text-right ltr:text-left bg-transparent dark:text-gray-100 outline-hidden w-full pt-2.5 pb-[5px] px-1 resize-none h-fit max-h-80 overflow-auto"
											id="chat-input-container"
										>
											<RichTextInput
												bind:this={chatInputElement}
												bind:value={prompt}
												id="chat-input"
												messageInput={true}
												shiftEnter={!($settings?.ctrlEnterToSend ?? false) &&
													(!$mobile ||
														!(
															'ontouchstart' in window ||
															navigator.maxTouchPoints > 0 ||
															navigator.msMaxTouchPoints > 0
														))}
												placeholder={placeholder ? placeholder : $i18n.t('Send a Message')}
												largeTextAsFile={($settings?.largeTextAsFile ?? false) && !shiftKey}
												autocomplete={$config?.features?.enable_autocomplete_generation &&
													($settings?.promptAutocomplete ?? false)}
												generateAutoCompletion={async (text) => {
													if (selectedModelIds.length === 0 || !selectedModelIds.at(0)) {
														toast.error($i18n.t('Please select a model first.'));
													}

													const res = await generateAutoCompletion(
														localStorage.token,
														selectedModelIds.at(0),
														text,
														history?.currentId
															? createMessagesList(history, history.currentId)
															: null
													).catch((error) => {
														console.log(error);

														return null;
													});

													console.log(res);
													return res;
												}}
												oncompositionstart={() => (isComposing = true)}
												oncompositionend={() => (isComposing = false)}
												on:keydown={async (e) => {
													e = e.detail.event;

													const isCtrlPressed = e.ctrlKey || e.metaKey; // metaKey is for Cmd key on Mac
													const commandsContainerElement =
														document.getElementById('commands-container');

													if (e.key === 'Escape') {
														stopResponse();
													}

													// Command/Ctrl + Shift + Enter to submit a message pair
													if (isCtrlPressed && e.key === 'Enter' && e.shiftKey) {
														e.preventDefault();
														createMessagePair(prompt);
													}

													// Check if Ctrl + R is pressed
													if (prompt === '' && isCtrlPressed && e.key.toLowerCase() === 'r') {
														e.preventDefault();
														console.log('regenerate');

														const regenerateButton = [
															...document.getElementsByClassName('regenerate-response-button')
														]?.at(-1);

														regenerateButton?.click();
													}

													if (prompt === '' && e.key == 'ArrowUp') {
														e.preventDefault();

														const userMessageElement = [
															...document.getElementsByClassName('user-message')
														]?.at(-1);

														if (userMessageElement) {
															userMessageElement.scrollIntoView({ block: 'center' });
															const editButton = [
																...document.getElementsByClassName('edit-user-message-button')
															]?.at(-1);

															editButton?.click();
														}
													}

													if (commandsContainerElement) {
														if (commandsContainerElement && e.key === 'ArrowUp') {
															e.preventDefault();
															commandsElement.selectUp();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);
															commandOptionButton.scrollIntoView({ block: 'center' });
														}

														if (commandsContainerElement && e.key === 'ArrowDown') {
															e.preventDefault();
															commandsElement.selectDown();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);
															commandOptionButton.scrollIntoView({ block: 'center' });
														}

														if (commandsContainerElement && e.key === 'Tab') {
															e.preventDefault();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);

															commandOptionButton?.click();
														}

														if (commandsContainerElement && e.key === 'Enter') {
															e.preventDefault();

															const commandOptionButton = [
																...document.getElementsByClassName('selected-command-option-button')
															]?.at(-1);

															if (commandOptionButton) {
																commandOptionButton?.click();
															} else {
																document.getElementById('send-message-button')?.click();
															}
														}
													} else {
														if (
															!$mobile ||
															!(
																'ontouchstart' in window ||
																navigator.maxTouchPoints > 0 ||
																navigator.msMaxTouchPoints > 0
															)
														) {
															if (isComposing) {
																return;
															}

															// Uses keyCode '13' for Enter key for chinese/japanese keyboards.
															//
															// Depending on the user's settings, it will send the message
															// either when Enter is pressed or when Ctrl+Enter is pressed.
															const enterPressed =
																($settings?.ctrlEnterToSend ?? false)
																	? (e.key === 'Enter' || e.keyCode === 13) && isCtrlPressed
																	: (e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey;

															if (enterPressed) {
																e.preventDefault();
																if (prompt !== '' || files.length > 0) {
																	dispatch('submit', prompt);
																}
															}
														}
													}

													if (e.key === 'Escape') {
														console.log('Escape');
														atSelectedModel = undefined;
														selectedToolIds = [];
														selectedFilterIds = [];

														webSearchEnabled = false;
														imageGenerationEnabled = false;
														codeInterpreterEnabled = false;
													}
												}}
												on:paste={async (e) => {
													e = e.detail.event;
													console.log(e);

													const clipboardData = e.clipboardData || window.clipboardData;

													if (clipboardData && clipboardData.items) {
														for (const item of clipboardData.items) {
															if (item.type.indexOf('image') !== -1) {
																const blob = item.getAsFile();
																const reader = new FileReader();

																reader.onload = function (e) {
																	files = [
																		...files,
																		{
																			type: 'image',
																			url: `${e.target.result}`
																		}
																	];
																};

																reader.readAsDataURL(blob);
															} else if (item.type === 'text/plain') {
																if (($settings?.largeTextAsFile ?? false) && !shiftKey) {
																	const text = clipboardData.getData('text/plain');

																	if (text.length > PASTED_TEXT_CHARACTER_LIMIT) {
																		e.preventDefault();
																		const blob = new Blob([text], { type: 'text/plain' });
																		const file = new File([blob], `Pasted_Text_${Date.now()}.txt`, {
																			type: 'text/plain'
																		});

																		await uploadFileHandler(file, true);
																	}
																}
															}
														}
													}
												}}
											/>
										</div>
									{:else}
										<textarea
											id="chat-input"
											dir={$settings?.chatDirection ?? 'auto'}
											bind:this={chatInputElement}
											class="scrollbar-hidden bg-transparent dark:text-gray-200 outline-hidden w-full pt-3 px-1 resize-none"
											placeholder={placeholder ? placeholder : $i18n.t('Send a Message')}
											bind:value={prompt}
											on:compositionstart={() => (isComposing = true)}
											on:compositionend={() => (isComposing = false)}
											on:keydown={async (e) => {
												const isCtrlPressed = e.ctrlKey || e.metaKey; // metaKey is for Cmd key on Mac

												const commandsContainerElement =
													document.getElementById('commands-container');

												if (e.key === 'Escape') {
													stopResponse();
												}

												// Command/Ctrl + Shift + Enter to submit a message pair
												if (isCtrlPressed && e.key === 'Enter' && e.shiftKey) {
													e.preventDefault();
													createMessagePair(prompt);
												}

												// Check if Ctrl + R is pressed
												if (prompt === '' && isCtrlPressed && e.key.toLowerCase() === 'r') {
													e.preventDefault();
													console.log('regenerate');

													const regenerateButton = [
														...document.getElementsByClassName('regenerate-response-button')
													]?.at(-1);

													regenerateButton?.click();
												}

												if (prompt === '' && e.key == 'ArrowUp') {
													e.preventDefault();

													const userMessageElement = [
														...document.getElementsByClassName('user-message')
													]?.at(-1);

													const editButton = [
														...document.getElementsByClassName('edit-user-message-button')
													]?.at(-1);

													console.log(userMessageElement);

													userMessageElement?.scrollIntoView({ block: 'center' });
													editButton?.click();
												}

												if (commandsContainerElement) {
													if (commandsContainerElement && e.key === 'ArrowUp') {
														e.preventDefault();
														commandsElement.selectUp();

														const container = document.getElementById('command-options-container');
														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);

														if (commandOptionButton && container) {
															const elTop = commandOptionButton.offsetTop;
															const elHeight = commandOptionButton.offsetHeight;
															const containerHeight = container.clientHeight;

															// Center the selected button in the container
															container.scrollTop = elTop - containerHeight / 2 + elHeight / 2;
														}
													}

													if (commandsContainerElement && e.key === 'ArrowDown') {
														e.preventDefault();
														commandsElement.selectDown();

														const container = document.getElementById('command-options-container');
														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);

														if (commandOptionButton && container) {
															const elTop = commandOptionButton.offsetTop;
															const elHeight = commandOptionButton.offsetHeight;
															const containerHeight = container.clientHeight;

															// Center the selected button in the container
															container.scrollTop = elTop - containerHeight / 2 + elHeight / 2;
														}
													}

													if (commandsContainerElement && e.key === 'Enter') {
														e.preventDefault();

														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);

														if (e.shiftKey) {
															prompt = `${prompt}\n`;
														} else if (commandOptionButton) {
															commandOptionButton?.click();
														} else {
															document.getElementById('send-message-button')?.click();
														}
													}

													if (commandsContainerElement && e.key === 'Tab') {
														e.preventDefault();

														const commandOptionButton = [
															...document.getElementsByClassName('selected-command-option-button')
														]?.at(-1);

														commandOptionButton?.click();
													}
												} else {
													if (
														!$mobile ||
														!(
															'ontouchstart' in window ||
															navigator.maxTouchPoints > 0 ||
															navigator.msMaxTouchPoints > 0
														)
													) {
														if (isComposing) {
															return;
														}

														// Prevent Enter key from creating a new line
														const isCtrlPressed = e.ctrlKey || e.metaKey;
														const enterPressed =
															($settings?.ctrlEnterToSend ?? false)
																? (e.key === 'Enter' || e.keyCode === 13) && isCtrlPressed
																: (e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey;

														if (enterPressed) {
															e.preventDefault();
														}

														// Submit the prompt when Enter key is pressed
														if ((prompt !== '' || files.length > 0) && enterPressed) {
															dispatch('submit', prompt);
														}
													}
												}

												if (e.key === 'Tab') {
													const words = extractCurlyBraceWords(prompt);

													if (words.length > 0) {
														const word = words.at(0);
														const fullPrompt = prompt;

														prompt = prompt.substring(0, word?.endIndex + 1);
														await tick();

														e.target.scrollTop = e.target.scrollHeight;
														prompt = fullPrompt;
														await tick();

														e.preventDefault();
														e.target.setSelectionRange(word?.startIndex, word.endIndex + 1);
													}

													e.target.style.height = '';
													e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
												}

												if (e.key === 'Escape') {
													console.log('Escape');
													atSelectedModel = undefined;
													selectedToolIds = [];
													selectedFilterIds = [];
													webSearchEnabled = false;
													imageGenerationEnabled = false;
													codeInterpreterEnabled = false;
												}
											}}
											rows="1"
											on:input={async (e) => {
												e.target.style.height = '';
												e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
											}}
											on:focus={async (e) => {
												e.target.style.height = '';
												e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
											}}
											on:paste={async (e) => {
												const clipboardData = e.clipboardData || window.clipboardData;

												if (clipboardData && clipboardData.items) {
													for (const item of clipboardData.items) {
														if (item.type.indexOf('image') !== -1) {
															const blob = item.getAsFile();
															const reader = new FileReader();

															reader.onload = function (e) {
																files = [
																	...files,
																	{
																		type: 'image',
																		url: `${e.target.result}`
																	}
																];
															};

															reader.readAsDataURL(blob);
														} else if (item.type === 'text/plain') {
															if (($settings?.largeTextAsFile ?? false) && !shiftKey) {
																const text = clipboardData.getData('text/plain');

																if (text.length > PASTED_TEXT_CHARACTER_LIMIT) {
																	e.preventDefault();
																	const blob = new Blob([text], { type: 'text/plain' });
																	const file = new File([blob], `Pasted_Text_${Date.now()}.txt`, {
																		type: 'text/plain'
																	});

																	await uploadFileHandler(file, true);
																}
															}
														}
													}
												}
											}}
										/>
									{/if}
								</div>

								<div class=" flex justify-between mt-0.5 mb-2.5 mx-0.5 max-w-full" dir="ltr">
									<div class="ml-1 self-end flex items-center flex-1 max-w-[80%]">
										<InputMenu
											bind:selectedToolIds
											selectedModels={atSelectedModel ? [atSelectedModel.id] : selectedModels}
											{fileUploadCapableModels}
											bind:structuredOutputEnabled
											{screenCaptureHandler}
											{inputFilesHandler}
											uploadFilesHandler={() => {
												filesInputElement.click();
											}}
											uploadGoogleDriveHandler={async () => {
												try {
													const fileData = await createPicker();
													if (fileData) {
														const file = new File([fileData.blob], fileData.name, {
															type: fileData.blob.type
														});
														await uploadFileHandler(file);
													} else {
														console.log('No file was selected from Google Drive');
													}
												} catch (error) {
													console.error('Google Drive Error:', error);
													toast.error(
														$i18n.t('Error accessing Google Drive: {{error}}', {
															error: error.message
														})
													);
												}
											}}
											uploadOneDriveHandler={async (authorityType) => {
												try {
													const fileData = await pickAndDownloadFile(authorityType);
													if (fileData) {
														const file = new File([fileData.blob], fileData.name, {
															type: fileData.blob.type || 'application/octet-stream'
														});
														await uploadFileHandler(file);
													} else {
														console.log('No file was selected from OneDrive');
													}
												} catch (error) {
													console.error('OneDrive Error:', error);
												}
											}}
											on:structuredOutputChange={(e) => {
												if (e.detail) {
													structuredOutputSchema = e.detail.schema;
													structuredOutputName = e.detail.name;
													structuredOutputEnabled = true;
													console.log('🎯 Structured Output Configured in MessageInput:', {
														schema: structuredOutputSchema,
														name: structuredOutputName,
														enabled: structuredOutputEnabled,
														schemaLength: structuredOutputSchema?.length || 0
													});
													
													// Force an update to the computed values
													displayStructuredOutput = structuredOutputEnabled || externalStructuredOutput;
													displayStructuredOutputSchema = structuredOutputSchema || externalStructuredOutputSchema;
													displayStructuredOutputName = structuredOutputName || externalStructuredOutputName;
													
													console.log('🎯 Computed values after configuration:', {
														displayStructuredOutput,
														displayStructuredOutputSchemaLength: displayStructuredOutputSchema?.length || 0,
														displayStructuredOutputName
													});
												} else {
													structuredOutputSchema = '';
													structuredOutputName = '';
													structuredOutputEnabled = false;
													console.log('🎯 Structured Output Cleared');
												}
											}}
											on:promptAttach={(e) => {
												attachedPrompt = e.detail;
												
												// Clear manual structured output when attaching a prompt
												// The prompt's own structured output (if any) will take precedence
												structuredOutputEnabled = false;
												structuredOutputSchema = '';
												structuredOutputName = '';
												
												console.log('🎯 Prompt attached:', {
													title: attachedPrompt.title || attachedPrompt.name,
													hasStructuredOutput: attachedPrompt.structured_output,
													clearedManualSO: true
												});
											}}
											onClose={async () => {
												await tick();

												const chatInput = document.getElementById('chat-input');
												chatInput?.focus();
											}}
										>
											<button
												class="bg-transparent hover:bg-gray-100 text-gray-800 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5 outline-hidden focus:outline-hidden"
												type="button"
												aria-label="More"
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 20 20"
													fill="currentColor"
													class="size-5"
												>
													<path
														d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z"
													/>
												</svg>
											</button>
										</InputMenu>

										{#if $_user && (showToolsButton || (toggleFilters && toggleFilters.length > 0) || showWebSearchButton || showImageGenerationButton || showCodeInterpreterButton || showStructuredOutputButton)}
											<div
												class="flex self-center w-[1px] h-4 mx-1.5 bg-gray-50 dark:bg-gray-800"
											/>

											<div class="flex gap-1 items-center overflow-x-auto scrollbar-none flex-1">
												{#if showToolsButton}
													<Tooltip
														content={$i18n.t('{{COUNT}} Available Tools', {
															COUNT: toolServers.length + selectedToolIds.length
														})}
													>
														<button
															class="translate-y-[0.5px] flex gap-1 items-center text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg p-1 self-center transition"
															aria-label="Available Tools"
															type="button"
															on:click={() => {
																showTools = !showTools;
															}}
														>
															<Wrench className="size-4" strokeWidth="1.75" />

															<span class="text-sm font-medium text-gray-600 dark:text-gray-300">
																{toolServers.length + selectedToolIds.length}
															</span>
														</button>
													</Tooltip>
												{/if}

												{#each toggleFilters as filter, filterIdx (filter.id)}
													<Tooltip content={filter?.description} placement="top">
														<button
															on:click|preventDefault={() => {
																if (selectedFilterIds.includes(filter.id)) {
																	selectedFilterIds = selectedFilterIds.filter(
																		(id) => id !== filter.id
																	);
																} else {
																	selectedFilterIds = [...selectedFilterIds, filter.id];
																}
															}}
															type="button"
															class="px-2 @xl:px-2.5 py-2 flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 {selectedFilterIds.includes(
																filter.id
															)
																? 'text-sky-500 dark:text-sky-300 bg-sky-50 dark:bg-sky-200/5'
																: 'bg-transparent text-gray-600 dark:text-gray-300  '} capitalize"
														>
															{#if filter?.icon}
																<div class="size-4 items-center flex justify-center">
																	<img
																		src={filter.icon}
																		class="size-3.5 {filter.icon.includes('svg')
																			? 'dark:invert-[80%]'
																			: ''}"
																		style="fill: currentColor;"
																		alt={filter.name}
																	/>
																</div>
															{:else}
																<Sparkles className="size-4" strokeWidth="1.75" />
															{/if}
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis leading-none pr-0.5"
																>{filter?.name}</span
															>
														</button>
													</Tooltip>
												{/each}

												{#if showWebSearchButton}
													<Tooltip content={$i18n.t('Search the internet')} placement="top">
														<button
															on:click|preventDefault={() => (webSearchEnabled = !webSearchEnabled)}
															type="button"
															class="px-2 @xl:px-2.5 py-2 flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 {webSearchEnabled ||
															($settings?.webSearch ?? false) === 'always'
																? ' text-sky-500 dark:text-sky-300 bg-sky-50 dark:bg-sky-200/5'
																: 'bg-transparent text-gray-600 dark:text-gray-300 '}"
														>
															<GlobeAlt className="size-4" strokeWidth="1.75" />
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis leading-none pr-0.5"
																>{$i18n.t('Web Search')}</span
															>
														</button>
													</Tooltip>
												{/if}

												{#if showStructuredOutputButton}
													<!-- Dedicated Structured Output Button -->
													<Tooltip 
														content={displayStructuredOutput 
															? `${$i18n.t('Structured Output Active')}: ${displayStructuredOutputName || 'Custom Schema'}\n${$i18n.t('Source')}: ${attachedPromptStructuredOutput ? $i18n.t('Attached Prompt') : externalStructuredOutput ? $i18n.t('External Command') : $i18n.t('Manual Configuration')}\n${$i18n.t('Click to edit')}`
															: $i18n.t('Configure structured output - Get JSON responses from AI models')} 
														placement="top"
													>
														<button
															on:click|preventDefault={() => {
																// Use the same mechanism as the current implementation
																const moreBtn = document.querySelector('[aria-label="More"]');
																if (moreBtn) {
																	moreBtn.click();
																	// Small delay to let the dropdown open, then click structured output
																	setTimeout(() => {
																		const structuredOutputBtn = document.querySelector('[data-structured-output-btn]');
																		if (structuredOutputBtn) {
																			structuredOutputBtn.click();
																		}
																	}, 50);
																}
															}}
															type="button"
															class="relative px-2 @xl:px-2.5 py-2 flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 {displayStructuredOutput
																? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-200/5'
																: 'bg-transparent text-gray-600 dark:text-gray-300'}"
														>
															<div class="relative">
																<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.75" stroke="currentColor" class="size-4">
																	<path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
																</svg>
																{#if displayStructuredOutput}
																	<!-- Active indicator dot -->
																	<div class="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full border border-white dark:border-gray-800"></div>
																{/if}
															</div>
															<span class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis leading-none pr-0.5">
																{#if displayStructuredOutput}
																	{#if attachedPromptStructuredOutput}
																		<span class="flex items-center gap-1">
																			{displayStructuredOutputName || 'JSON'}
																			<span class="text-xs opacity-75">📎</span>
																		</span>
																	{:else if externalStructuredOutput}
																		<span class="flex items-center gap-1">
																			{displayStructuredOutputName || 'JSON'}
																			<span class="text-xs opacity-75">⌘</span>
																		</span>
																	{:else}
																		{displayStructuredOutputName || 'JSON'}
																	{/if}
																{:else}
																	{$i18n.t('JSON')}
																{/if}
															</span>
														</button>
													</Tooltip>
												{/if}

												{#if showImageGenerationButton}
													<Tooltip content={$i18n.t('Generate an image')} placement="top">
														<button
															on:click|preventDefault={() =>
																(imageGenerationEnabled = !imageGenerationEnabled)}
															type="button"
															class="px-2 @xl:px-2.5 py-2 flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 {imageGenerationEnabled
																? ' text-sky-500 dark:text-sky-300 bg-sky-50 dark:bg-sky-200/5'
																: 'bg-transparent text-gray-600 dark:text-gray-300 '}"
														>
															<Photo className="size-4" strokeWidth="1.75" />
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis leading-none pr-0.5"
																>{$i18n.t('Image')}</span
															>
														</button>
													</Tooltip>
												{/if}

												{#if showCodeInterpreterButton}
													<Tooltip content={$i18n.t('Execute code for analysis')} placement="top">
														<button
															on:click|preventDefault={() =>
																(codeInterpreterEnabled = !codeInterpreterEnabled)}
															type="button"
															class="px-2 @xl:px-2.5 py-2 flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 {codeInterpreterEnabled
																? ' text-sky-500 dark:text-sky-300 bg-sky-50 dark:bg-sky-200/5'
																: 'bg-transparent text-gray-600 dark:text-gray-300 '}"
														>
															<CommandLine className="size-4" strokeWidth="1.75" />
															<span
																class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis leading-none pr-0.5"
																>{$i18n.t('Code Interpreter')}</span
															>
														</button>
													</Tooltip>
												{/if}
											</div>
										{/if}
									</div>

									<div class="self-end flex space-x-1 mr-1 shrink-0">
										{#if (!history?.currentId || history.messages[history.currentId]?.done == true) && ($_user?.role === 'admin' || ($_user?.permissions?.chat?.stt ?? true))}
											<!-- {$i18n.t('Record voice')} -->
											<Tooltip content={$i18n.t('Dictate')}>
												<button
													id="voice-input-button"
													class=" text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5 mr-0.5 self-center"
													type="button"
													on:click={async () => {
														try {
															let stream = await navigator.mediaDevices
																.getUserMedia({ audio: true })
																.catch(function (err) {
																	toast.error(
																		$i18n.t(
																			`Permission denied when accessing microphone: {{error}}`,
																			{
																				error: err
																			}
																		)
																	);
																	return null;
																});

															if (stream) {
																recording = true;
																const tracks = stream.getTracks();
																tracks.forEach((track) => track.stop());
															}
															stream = null;
														} catch {
															toast.error($i18n.t('Permission denied when accessing microphone'));
														}
													}}
													aria-label="Voice Input"
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														viewBox="0 0 20 20"
														fill="currentColor"
														class="w-5 h-5 translate-y-[0.5px]"
													>
														<path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
														<path
															d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z"
														/>
													</svg>
												</button>
											</Tooltip>
										{/if}

										{#if (taskIds && taskIds.length > 0) || (history.currentId && history.messages[history.currentId]?.done != true)}
											<div class=" flex items-center">
												<Tooltip content={$i18n.t('Stop')}>
													<button
														class="bg-white hover:bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5"
														on:click={() => {
															stopResponse();
														}}
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 24 24"
															fill="currentColor"
															class="size-5"
														>
															<path
																fill-rule="evenodd"
																d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm6-2.438c0-.724.588-1.312 1.313-1.312h4.874c.725 0 1.313.588 1.313 1.313v4.874c0 .725-.588 1.313-1.313 1.313H9.564a1.312 1.312 0 01-1.313-1.313V9.564z"
																clip-rule="evenodd"
															/>
														</svg>
													</button>
												</Tooltip>
											</div>
										{:else if prompt === '' && files.length === 0 && ($_user?.role === 'admin' || ($_user?.permissions?.chat?.call ?? true))}
											<div class=" flex items-center">
												<!-- {$i18n.t('Call')} -->
												<Tooltip content={$i18n.t('Voice mode')}>
													<button
														class=" bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full p-1.5 self-center"
														type="button"
														on:click={async () => {
															if (selectedModels.length > 1) {
																toast.error($i18n.t('Select only one model to call'));

																return;
															}

															if ($config.audio.stt.engine === 'web') {
																toast.error(
																	$i18n.t('Call feature is not supported when using Web STT engine')
																);

																return;
															}
															// check if user has access to getUserMedia
															try {
																let stream = await navigator.mediaDevices.getUserMedia({
																	audio: true
																});
																// If the user grants the permission, proceed to show the call overlay

																if (stream) {
																	const tracks = stream.getTracks();
																	tracks.forEach((track) => track.stop());
																}

																stream = null;

																if ($settings.audio?.tts?.engine === 'browser-kokoro') {
																	// If the user has not initialized the TTS worker, initialize it
																	if (!$TTSWorker) {
																		await TTSWorker.set(
																			new KokoroWorker({
																				dtype: $settings.audio?.tts?.engineConfig?.dtype ?? 'fp32'
																			})
																		);

																		await $TTSWorker.init();
																	}
																}

																showCallOverlay.set(true);
																showControls.set(true);
															} catch (err) {
																// If the user denies the permission or an error occurs, show an error message
																toast.error(
																	$i18n.t('Permission denied when accessing media devices')
																);
															}
														}}
														aria-label="Call"
													>
														<Headphone className="size-5" />
													</button>
												</Tooltip>
											</div>
										{:else}
											<div class=" flex items-center">
												<Tooltip content={$i18n.t('Send message')}>
													<button
														id="send-message-button"
														class="{!(prompt === '' && files.length === 0)
															? 'bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 '
															: 'text-white bg-gray-200 dark:text-gray-900 dark:bg-gray-700 disabled'} transition rounded-full p-1.5 self-center"
														type="submit"
														disabled={prompt === '' && files.length === 0}
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 16 16"
															fill="currentColor"
															class="size-5"
														>
															<path
																fill-rule="evenodd"
																d="M8 14a.75.75 0 0 1-.75-.75V4.56L4.03 7.78a.75.75 0 0 1-1.06-1.06l4.5-4.5a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06L8.75 4.56v8.69A.75.75 0 0 1 8 14Z"
																clip-rule="evenodd"
															/>
														</svg>
													</button>
												</Tooltip>
											</div>
										{/if}
									</div>
								</div>
							</div>

							{#if $config?.license_metadata?.input_footer}
								<div class=" text-xs text-gray-500 text-center line-clamp-1 marked">
									{@html DOMPurify.sanitize(marked($config?.license_metadata?.input_footer))}
								</div>
							{:else}
								<div class="mb-1" />
							{/if}
						</form>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
