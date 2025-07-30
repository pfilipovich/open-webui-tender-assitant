<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy, getContext } from 'svelte';
  import { validateJsonSchema, getSchemaTemplates } from '$lib/utils/schema-validation';
  import Textarea from '$lib/components/common/Textarea.svelte';
  import { flyAndScale } from '$lib/utils/transitions';
  import { 
    createModalEventBoundary, 
    safeModalOperation, 
    withStateLock,
    enableEventProtectionDebug 
  } from '$lib/utils/event-protection';
  import SchemaLibraryModal from './SchemaLibraryModal.svelte';

  const dispatch = createEventDispatcher();
  const i18n = getContext('i18n');

  export let show = false;
  export let currentSchema = '';
  export let currentName = '';

  let schema = '';
  let schemaName = '';
  let validationResult = { valid: true };
  let templates = getSchemaTemplates();
  let modalElement: HTMLElement;
  let cleanupModalBoundary: (() => void) | null = null;
  let showSchemaLibrary = false;

  onMount(() => {
    schema = currentSchema || '';
    schemaName = currentName || '';
    validateSchema();
    
    // Debug template loading
    console.log('📋 Available templates:', templates);
    console.log('📋 Template count:', Object.keys(templates).length);
    
    // Enable debug mode in development
    if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      enableEventProtectionDebug(true);
    }
  });

  // Reactive setup for modal event boundary
  $: if (modalElement && show) {
    // Clean up existing boundary
    if (cleanupModalBoundary) {
      cleanupModalBoundary();
    }
    // Set up new modal event boundary
    cleanupModalBoundary = createModalEventBoundary(modalElement);
  }

  onDestroy(() => {
    // Clean up modal event boundary
    if (cleanupModalBoundary) {
      cleanupModalBoundary();
      cleanupModalBoundary = null;
    }
  });

  const validateSchema = () => {
    validationResult = validateJsonSchema(schema, { 
      enableOpenAIValidation: true, 
      strictMode: false 
    });
  };

  const selectTemplate = (templateKey) => {
    console.log('🎯 Template selected:', templateKey);
    const template = templates[templateKey];
    console.log('🎯 Template data:', template);
    
    if (template) { 
      schema = template.schema;
      schemaName = template.name;
      console.log('🎯 Schema set:', { schema: schema.substring(0, 100) + '...', name: schemaName });
      validateSchema();
    } else {
      console.error('🎯 Template not found:', templateKey, 'Available:', Object.keys(templates));
    }
  };

  const handleSave = () => {
    if (!validationResult.valid) return;
    
    dispatch('save', {
      schema: schema.trim(),
      name: schemaName || 'Custom Schema',
      templateKey: Object.keys(templates).find(key => 
        templates[key].schema === schema
      ) || 'custom'
    });
    show = false;
  };

  const handleCancel = () => {
    dispatch('cancel');
    show = false;
  };

  const handleClear = () => {
    schema = '';
    schemaName = '';
    validationResult = { valid: true };
    dispatch('clear');
    show = false;
  };

  const handleSchemaFromLibrary = (event) => {
    schema = event.detail.schema;
    schemaName = event.detail.name;
    validateSchema();
    showSchemaLibrary = false;
  };
</script>

{#if show}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
       transition:flyAndScale
       on:click={(e) => {
         if (e.target === e.currentTarget) {
           e.preventDefault();
           e.stopPropagation();
           handleCancel();
         }
       }}>
    <div bind:this={modalElement}
         class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
         on:click={(e) => {
           e.stopPropagation();
         }}>
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
          {$i18n.t('Configure Structured Output')}
        </h2>
        <button 
          type="button"
          on:click={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleCancel();
          }}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Schema Name -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {$i18n.t('Schema Name')}
        </label>
        <input
          type="text"
          bind:value={schemaName}
          placeholder={$i18n.t('Enter schema name')}
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
      </div>

      <!-- Template Selection and Schema Library -->
      <div class="mb-4">
        <div class="flex justify-between items-center mb-2">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {$i18n.t('Quick Templates')}
          </label>
          <button
            type="button"
            on:click={(e) => {
              e.preventDefault();
              e.stopPropagation();
              showSchemaLibrary = true;
            }}
            class="px-3 py-1.5 text-sm bg-blue-100 hover:bg-blue-200 dark:bg-blue-800 dark:hover:bg-blue-700 
                   text-blue-700 dark:text-blue-300 rounded-md transition flex items-center gap-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
            </svg>
            Browse Library
          </button>
        </div>
        <div class="flex gap-2 flex-wrap">
          {#each Object.entries(templates) as [key, template]}
            <button
              type="button"
              on:click={(e) => {
                e.preventDefault();
                e.stopPropagation();
                selectTemplate(key);
              }}
              class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 
                     dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md transition"
            >
              {template.name}
            </button>
          {:else}
            <div class="text-sm text-gray-500 dark:text-gray-400">
              No templates available (Debug: {Object.keys(templates).length} found)
            </div>
          {/each}
        </div>
      </div>

      <!-- Schema Editor -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {$i18n.t('JSON Schema')}
        </label>
        <Textarea
          bind:value={schema}
          on:input={validateSchema}
          placeholder={$i18n.t('Enter your JSON schema or select a template')}
          rows={12}
          className="font-mono text-sm {validationResult.valid ? '' : 'border-red-500'}"
        />
        
        <!-- Validation Feedback -->
        <div class="mt-2 space-y-2">
          {#if !validationResult.valid}
            <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p class="text-red-700 dark:text-red-300 text-sm font-medium">
                ❌ {validationResult.error}
              </p>
            </div>
          {:else if schema.trim()}
            <div class="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <p class="text-green-700 dark:text-green-300 text-sm font-medium">
                ✅ {$i18n.t('Valid JSON schema')}
              </p>
              
              {#if validationResult.stats}
                <div class="mt-2 text-xs text-green-600 dark:text-green-400 space-y-1">
                  <div class="flex justify-between">
                    <span>Properties:</span>
                    <span>{validationResult.stats.totalProperties} / 5,000</span>
                  </div>
                  <div class="flex justify-between">
                    <span>Nesting depth:</span>
                    <span>{validationResult.stats.maxNestingDepth} / 5</span>
                  </div>
                  <div class="flex justify-between">
                    <span>String length:</span>
                    <span>{validationResult.stats.totalStringLength.toLocaleString()} / 120,000</span>
                  </div>
                  {#if validationResult.stats.enumCount > 0}
                    <div class="flex justify-between">
                      <span>Enum values:</span>
                      <span>{validationResult.stats.enumCount} / 1,000</span>
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
          
          {#if validationResult.warnings && validationResult.warnings.length > 0}
            <div class="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p class="text-yellow-700 dark:text-yellow-300 text-sm font-medium mb-2">
                ⚠️ OpenAI Compatibility Warnings:
              </p>
              <ul class="text-sm text-yellow-600 dark:text-yellow-400 space-y-1">
                {#each validationResult.warnings as warning}
                  <li class="flex items-start">
                    <span class="inline-block w-1 h-1 bg-yellow-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                    <span>{warning}</span>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-between">
        <button
          type="button"
          on:click={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleClear();
          }}
          class="px-4 py-2 text-sm text-red-600 hover:text-red-700 
                 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 
                 rounded-md transition"
        >
          {$i18n.t('Clear')}
        </button>
        
        <div class="flex gap-2">
          <button
            type="button"
            on:click={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleCancel();
            }}
            class="px-4 py-2 text-sm text-gray-600 hover:text-gray-700 
                   bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 
                   rounded-md transition"
          >
            {$i18n.t('Cancel')}
          </button>
          
          <button
            type="button"
            on:click={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleSave();
            }}
            disabled={!validationResult.valid}
            class="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 
                   disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md transition"
          >
            {$i18n.t('Save Schema')}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Schema Library Modal -->
<SchemaLibraryModal 
  bind:show={showSchemaLibrary}
  on:select={handleSchemaFromLibrary}
/>