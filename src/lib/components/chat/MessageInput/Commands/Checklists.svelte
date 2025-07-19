<script lang="ts">
    import { checklists, settings, user } from '$lib/stores';
    import { getChecklistByCommand } from '$lib/apis/checklists';
    import { getPromptByCommand } from '$lib/apis/prompts';
    import { toast } from 'svelte-sonner';
    import { tick, getContext, createEventDispatcher } from 'svelte';
    import {
        extractCurlyBraceWords,
        getUserPosition,
        getFormattedDate,
        getFormattedTime,
        getCurrentDateTime,
        getUserTimezone,
        getWeekday
    } from '$lib/utils';

    const dispatch = createEventDispatcher();
    const i18n = getContext('i18n');

    export let files = [];
    export let prompt = '';
    export let command = '';

    let selectedChecklistIdx = 0;
    let filteredChecklists = [];

    $: filteredChecklists = $checklists
        .filter((c) => c.command.toLowerCase().includes(command.toLowerCase()))
        .sort((a, b) => a.title.localeCompare(b.title));

    $: if (command) {
        selectedChecklistIdx = 0;
    }

    export const selectUp = () => {
        selectedChecklistIdx = Math.max(0, selectedChecklistIdx - 1);
    };

    export const selectDown = () => {
        selectedChecklistIdx = Math.min(selectedChecklistIdx + 1, filteredChecklists.length - 1);
    };

    const executeChecklist = async (checklist) => {
        console.log('Executing checklist:', checklist);
        
        try {
            // Get full checklist with items
            const fullChecklist = await getChecklistByCommand(localStorage.token, checklist.command);
            
            if (!fullChecklist || !fullChecklist.items || fullChecklist.items.length === 0) {
                toast.error($i18n.t('Checklist has no prompts to execute'));
                return;
            }

            // Sort items by order_index
            const sortedItems = fullChecklist.items.sort((a, b) => a.order_index - b.order_index);
            
            let aggregatedResponse = `# ${fullChecklist.title}\n\n`;
            if (fullChecklist.description) {
                aggregatedResponse += `${fullChecklist.description}\n\n---\n\n`;
            }

            // Execute each prompt in sequence
            for (let i = 0; i < sortedItems.length; i++) {
                const item = sortedItems[i];
                
                try {
                    // Get the prompt
                    const promptData = await getPromptByCommand(localStorage.token, item.prompt_command);
                    if (!promptData) {
                        aggregatedResponse += `**${i + 1}. ${item.prompt_command}** - ❌ Prompt not found\n\n`;
                        continue;
                    }

                    // Process prompt content with variables
                    let processedContent = await processPromptVariables(promptData.content, aggregatedResponse);
                    
                    aggregatedResponse += `**${i + 1}. ${promptData.title}** (${item.prompt_command})\n\n`;
                    aggregatedResponse += `${processedContent}\n\n---\n\n`;
                    
                } catch (error) {
                    console.error('Error executing prompt:', item.prompt_command, error);
                    aggregatedResponse += `**${i + 1}. ${item.prompt_command}** - ❌ Error: ${error.message}\n\n`;
                }
            }

            // Replace the command in prompt with the aggregated response
            const lines = prompt.split('\n');
            const lastLine = lines.pop();
            const lastLineWords = lastLine.split(' ');
            lastLineWords.pop(); // Remove the checklist command

            if ($settings?.richTextInput ?? true) {
                lastLineWords.push(
                    `${aggregatedResponse.replace(/</g, '&lt;').replace(/>/g, '&gt;').replaceAll('\n', '<br/>')}`
                );
                lines.push(lastLineWords.join(' '));
                prompt = lines.join('<br/>');
            } else {
                lastLineWords.push(aggregatedResponse);
                lines.push(lastLineWords.join(' '));
                prompt = lines.join('\n');
            }

            // Focus the chat input
            await tick();
            const chatInputElement = document.getElementById('chat-input');
            if (chatInputElement) {
                chatInputElement.focus();
                chatInputElement.dispatchEvent(new Event('input'));
                chatInputElement.scrollTop = chatInputElement.scrollHeight;
            }

        } catch (error) {
            console.error('Error executing checklist:', error);
            toast.error($i18n.t('Failed to execute checklist'));
        }
    };

    const processPromptVariables = async (content, previousResponses = '') => {
        let text = content;

        // Standard variables (same as Prompts)
        if (text.includes('{{CLIPBOARD}}')) {
            try {
                const clipboardText = await navigator.clipboard.readText();
                text = text.replaceAll('{{CLIPBOARD}}', clipboardText);
            } catch {
                text = text.replaceAll('{{CLIPBOARD}}', '');
            }
        }

        if (text.includes('{{USER_NAME}}')) {
            const name = $user?.name || 'User';
            text = text.replaceAll('{{USER_NAME}}', name);
        }

        if (text.includes('{{USER_LANGUAGE}}')) {
            const language = localStorage.getItem('locale') || 'en-US';
            text = text.replaceAll('{{USER_LANGUAGE}}', language);
        }

        if (text.includes('{{CURRENT_DATE}}')) {
            const date = getFormattedDate();
            text = text.replaceAll('{{CURRENT_DATE}}', date);
        }

        if (text.includes('{{CURRENT_TIME}}')) {
            const time = getFormattedTime();
            text = text.replaceAll('{{CURRENT_TIME}}', time);
        }

        if (text.includes('{{CURRENT_DATETIME}}')) {
            const dateTime = getCurrentDateTime();
            text = text.replaceAll('{{CURRENT_DATETIME}}', dateTime);
        }

        if (text.includes('{{CURRENT_TIMEZONE}}')) {
            const timezone = getUserTimezone();
            text = text.replaceAll('{{CURRENT_TIMEZONE}}', timezone);
        }

        if (text.includes('{{CURRENT_WEEKDAY}}')) {
            const weekday = getWeekday();
            text = text.replaceAll('{{CURRENT_WEEKDAY}}', weekday);
        }

        // Checklist-specific variables
        if (text.includes('{{PREVIOUS_RESPONSES}}')) {
            text = text.replaceAll('{{PREVIOUS_RESPONSES}}', previousResponses);
        }

        if (text.includes('{{FILE_NAMES}}')) {
            const fileNames = files.map(f => f.name || 'Unknown file').join(', ');
            text = text.replaceAll('{{FILE_NAMES}}', fileNames);
        }

        return text;
    };
</script>

{#if filteredChecklists.length > 0}
    <div
        id="checklists-container"
        class="px-2 mb-2 text-left w-full absolute bottom-0 left-0 right-0 z-10"
    >
        <div class="flex w-full rounded-xl border border-gray-100 dark:border-gray-850">
            <div class="flex flex-col w-full rounded-xl bg-white dark:bg-gray-900 dark:text-gray-100">
                <div
                    class="m-1 overflow-y-auto p-1 space-y-0.5 scrollbar-hidden max-h-60"
                    id="checklist-options-container"
                >
                    {#each filteredChecklists as checklist, checklistIdx}
                        <button
                            class="px-3 py-1.5 rounded-xl w-full text-left {checklistIdx === selectedChecklistIdx
                                ? 'bg-gray-50 dark:bg-gray-850 selected-command-option-button'
                                : ''}"
                            type="button"
                            on:click={() => {
                                executeChecklist(checklist);
                            }}
                            on:mousemove={() => {
                                selectedChecklistIdx = checklistIdx;
                            }}
                            on:focus={() => {}}
                        >
                            <div class="font-medium text-black dark:text-gray-100 flex items-center">
                                <span class="mr-2">%</span>
                                {checklist.command}
                                <span class="ml-auto text-xs text-gray-500">
                                    {checklist.items?.length || 0} prompts
                                </span>
                            </div>

                            <div class="text-xs text-gray-600 dark:text-gray-100">
                                {checklist.title}
                            </div>
                        </button>
                    {/each}
                </div>

                <div
                    class="px-2 pt-0.5 pb-1 text-xs text-gray-600 dark:text-gray-100 bg-white dark:bg-gray-900 rounded-b-xl flex items-center space-x-1"
                >
                    <div>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke-width="1.5"
                            stroke="currentColor"
                            class="w-3 h-3"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                    </div>

                    <div class="line-clamp-1">
                        {$i18n.t('Execute multiple prompts in sequence. Variables and context are preserved between prompts.')}
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}