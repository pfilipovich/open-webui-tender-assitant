<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { flyAndScale } from '$lib/utils/transitions';
  import { 
    getSchemaLibrary, 
    addSchemaToLibrary, 
    updateSchemaInLibrary, 
    deleteSchemaFromLibrary,
    searchSchemas,
    exportSchemasToJSON,
    importSchemasFromJSON,
    incrementSchemaUsage,
    getPopularSchemas,
    getRecentSchemas,
    type SchemaLibraryItem 
  } from '$lib/utils/schema-library';
  import { validateJsonSchema } from '$lib/utils/schema-validation';
  import Textarea from '$lib/components/common/Textarea.svelte';

  const dispatch = createEventDispatcher();

  export let show = false;

  let activeTab: 'browse' | 'manage' | 'import-export' = 'browse';
  let searchQuery = '';
  let selectedCategory: 'all' | 'built-in' | 'user' | 'imported' = 'all';
  let schemas: SchemaLibraryItem[] = [];
  let filteredSchemas: SchemaLibraryItem[] = [];
  let popularSchemas: SchemaLibraryItem[] = [];
  let recentSchemas: SchemaLibraryItem[] = [];

  // Schema editing state
  let editingSchema: SchemaLibraryItem | null = null;
  let isCreatingNew = false;
  let editForm = {
    name: '',
    description: '',
    schema: '',
    tags: '',
    isPublic: false
  };

  // Import/Export state
  let importData = '';
  let importResult: { imported: number; skipped: number; errors: string[] } | null = null;
  let exportResult = '';

  onMount(() => {
    loadSchemas();
  });

  const loadSchemas = () => {
    const library = getSchemaLibrary();
    schemas = library.schemas;
    popularSchemas = getPopularSchemas(3);
    recentSchemas = getRecentSchemas(3);
    filterSchemas();
  };

  const filterSchemas = () => {
    let filtered = schemas;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(s => s.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      filtered = searchSchemas(searchQuery, selectedCategory === 'all' ? undefined : selectedCategory);
    }

    filteredSchemas = filtered;
  };

  const handleSelectSchema = (schema: SchemaLibraryItem) => {
    incrementSchemaUsage(schema.id);
    dispatch('select', {
      name: schema.name,
      schema: schema.schema
    });
    show = false;
  };

  const startEditing = (schema: SchemaLibraryItem) => {
    editingSchema = schema;
    isCreatingNew = false;
    editForm = {
      name: schema.name,
      description: schema.description,
      schema: schema.schema,
      tags: schema.tags.join(', '),
      isPublic: schema.isPublic
    };
  };

  const startCreatingNew = () => {
    editingSchema = null;
    isCreatingNew = true;
    editForm = {
      name: '',
      description: '',
      schema: '{\n  "type": "object",\n  "properties": {\n    \n  },\n  "required": []\n}',
      tags: '',
      isPublic: false
    };
  };

  const saveSchema = () => {
    const validation = validateJsonSchema(editForm.schema);
    if (!validation.valid) {
      alert(`Invalid schema: ${validation.error}`);
      return;
    }

    try {
      if (isCreatingNew) {
        addSchemaToLibrary(
          editForm.name,
          editForm.description,
          editForm.schema,
          {
            tags: editForm.tags.split(',').map(t => t.trim()).filter(t => t),
            isPublic: editForm.isPublic
          }
        );
      } else if (editingSchema) {
        updateSchemaInLibrary(editingSchema.id, {
          name: editForm.name,
          description: editForm.description,
          schema: editForm.schema,
          tags: editForm.tags.split(',').map(t => t.trim()).filter(t => t),
          isPublic: editForm.isPublic
        });
      }
      
      loadSchemas();
      cancelEditing();
    } catch (error) {
      alert(`Error saving schema: ${error.message}`);
    }
  };

  const deleteSchema = (schema: SchemaLibraryItem) => {
    if (confirm(`Are you sure you want to delete "${schema.name}"?`)) {
      try {
        deleteSchemaFromLibrary(schema.id);
        loadSchemas();
      } catch (error) {
        alert(`Error deleting schema: ${error.message}`);
      }
    }
  };

  const cancelEditing = () => {
    editingSchema = null;
    isCreatingNew = false;
  };

  const exportSchemas = () => {
    const userSchemas = schemas.filter(s => s.category === 'user');
    if (userSchemas.length === 0) {
      alert('No user schemas to export');
      return;
    }
    exportResult = exportSchemasToJSON();
  };

  const importSchemas = () => {
    if (!importData.trim()) {
      alert('Please enter JSON data to import');
      return;
    }

    try {
      importResult = importSchemasFromJSON(importData);
      if (importResult.imported > 0) {
        loadSchemas();
      }
    } catch (error) {
      alert(`Import failed: ${error.message}`);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    });
  };

  $: {
    filterSchemas();
  }
</script>

{#if show}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
       transition:flyAndScale>
    <div class="bg-white dark:bg-gray-800 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
          Schema Library
        </h2>
        <button 
          on:click={() => show = false} 
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-gray-200 dark:border-gray-700">
        <button 
          class="px-6 py-3 text-sm font-medium {activeTab === 'browse' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
          on:click={() => activeTab = 'browse'}
        >
          Browse Schemas
        </button>
        <button 
          class="px-6 py-3 text-sm font-medium {activeTab === 'manage' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
          on:click={() => activeTab = 'manage'}
        >
          Manage Schemas
        </button>
        <button 
          class="px-6 py-3 text-sm font-medium {activeTab === 'import-export' ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
          on:click={() => activeTab = 'import-export'}
        >
          Import / Export
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
        {#if activeTab === 'browse'}
          <!-- Browse Tab -->
          <div class="space-y-6">
            <!-- Search and Filter -->
            <div class="flex gap-4">
              <div class="flex-1">
                <input
                  type="text"
                  bind:value={searchQuery}
                  placeholder="Search schemas..."
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <select 
                bind:value={selectedCategory}
                class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="all">All Categories</option>
                <option value="built-in">Built-in</option>
                <option value="user">My Schemas</option>
                <option value="imported">Imported</option>
              </select>
            </div>

            <!-- Quick Access -->
            {#if popularSchemas.length > 0 || recentSchemas.length > 0}
              <div class="grid md:grid-cols-2 gap-6">
                {#if popularSchemas.length > 0}
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">Popular Schemas</h3>
                    <div class="space-y-2">
                      {#each popularSchemas as schema}
                        <button
                          on:click={() => handleSelectSchema(schema)}
                          class="w-full text-left p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                          <div class="font-medium text-gray-900 dark:text-white">{schema.name}</div>
                          <div class="text-sm text-gray-500 dark:text-gray-400">{schema.description}</div>
                        </button>
                      {/each}
                    </div>
                  </div>
                {/if}

                {#if recentSchemas.length > 0}
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">Recently Used</h3>
                    <div class="space-y-2">
                      {#each recentSchemas as schema}
                        <button
                          on:click={() => handleSelectSchema(schema)}
                          class="w-full text-left p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                          <div class="font-medium text-gray-900 dark:text-white">{schema.name}</div>
                          <div class="text-sm text-gray-500 dark:text-gray-400">{schema.description}</div>
                        </button>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            {/if}

            <!-- All Schemas -->
            <div>
              <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-3">
                All Schemas ({filteredSchemas.length})
              </h3>
              <div class="grid gap-4">
                {#each filteredSchemas as schema}
                  <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div class="flex justify-between items-start">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                          <h4 class="font-medium text-gray-900 dark:text-white">{schema.name}</h4>
                          <span class="px-2 py-1 text-xs rounded {
                            schema.category === 'built-in' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400' :
                            schema.category === 'user' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                            'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
                          }">
                            {schema.category}
                          </span>
                        </div>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">{schema.description}</p>
                        {#if schema.tags.length > 0}
                          <div class="flex gap-1 flex-wrap">
                            {#each schema.tags as tag}
                              <span class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                                {tag}
                              </span>
                            {/each}
                          </div>
                        {/if}
                      </div>
                      <button
                        on:click={() => handleSelectSchema(schema)}
                        class="ml-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition"
                      >
                        Use Schema
                      </button>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          </div>

        {:else if activeTab === 'manage'}
          <!-- Manage Tab -->
          <div class="space-y-6">
            {#if isCreatingNew || editingSchema}
              <!-- Schema Editor -->
              <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  {isCreatingNew ? 'Create New Schema' : 'Edit Schema'}
                </h3>
                
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Name</label>
                    <input
                      type="text" 
                      bind:value={editForm.name}
                      class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  
                  <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</label>
                    <input
                      type="text"
                      bind:value={editForm.description}
                      class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  
                  <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Schema</label>
                    <Textarea
                      bind:value={editForm.schema}
                      rows={12}
                      className="font-mono text-sm w-full"
                    />
                  </div>
                  
                  <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Tags (comma-separated)</label>
                    <input
                      type="text"
                      bind:value={editForm.tags}
                      placeholder="tag1, tag2, tag3"
                      class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  
                  <div class="flex items-center">
                    <input
                      type="checkbox"
                      id="isPublic"
                      bind:checked={editForm.isPublic}
                      class="rounded border-gray-300 dark:border-gray-600"
                    />
                    <label for="isPublic" class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Make this schema public
                    </label>
                  </div>
                </div>
                
                <div class="flex gap-2 mt-6">
                  <button
                    on:click={saveSchema}
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition"
                  >
                    Save Schema
                  </button>
                  <button
                    on:click={cancelEditing}
                    class="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-700 text-sm rounded-md transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            {:else}
              <!-- Schema List -->
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">Your Schemas</h3>
                <button
                  on:click={startCreatingNew}
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition"
                >
                  Create New Schema
                </button>
              </div>
              
              <div class="grid gap-4">
                {#each schemas.filter(s => s.category !== 'built-in') as schema}
                  <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div class="flex justify-between items-start">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                          <h4 class="font-medium text-gray-900 dark:text-white">{schema.name}</h4>
                          <span class="px-2 py-1 text-xs rounded {
                            schema.category === 'user' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                            'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
                          }">
                            {schema.category}
                          </span>
                          {#if schema.usage_count && schema.usage_count > 0}
                            <span class="text-xs text-gray-500 dark:text-gray-400">
                              Used {schema.usage_count} times
                            </span>
                          {/if}
                        </div>
                        <p class="text-sm text-gray-600 dark:text-gray-400">{schema.description}</p>
                      </div>
                      <div class="flex gap-2 ml-4">
                        <button
                          on:click={() => startEditing(schema)}
                          class="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          Edit
                        </button>
                        <button
                          on:click={() => deleteSchema(schema)}
                          class="px-3 py-1 text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

        {:else if activeTab === 'import-export'}
          <!-- Import/Export Tab -->
          <div class="space-y-6">
            <!-- Export Section -->
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Export Schemas</h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Export your custom schemas to share with others or backup.
              </p>
              
              <button
                on:click={exportSchemas}
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition"
              >
                Export My Schemas
              </button>
              
              {#if exportResult}
                <div class="mt-4">
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Exported JSON:
                  </label>
                  <div class="relative">
                    <Textarea
                      value={exportResult}
                      rows={10}
                      className="font-mono text-sm w-full"
                      readonly
                    />
                    <button
                      on:click={() => copyToClipboard(exportResult)}
                      class="absolute top-2 right-2 px-2 py-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-xs rounded"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              {/if}
            </div>
            
            <!-- Import Section -->
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Import Schemas</h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Import schemas from JSON data. Paste the exported JSON below.
              </p>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    JSON Data:
                  </label>
                  <Textarea
                    bind:value={importData}
                    rows={8}
                    className="font-mono text-sm w-full"
                    placeholder="Paste your exported schema JSON here..."
                  />
                </div>
                
                <button
                  on:click={importSchemas}
                  class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-md transition"
                >
                  Import Schemas
                </button>
              </div>
              
              {#if importResult}
                <div class="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <h4 class="font-medium text-gray-900 dark:text-white mb-2">Import Results:</h4>
                  <ul class="text-sm space-y-1">
                    <li class="text-green-600 dark:text-green-400">✓ Imported: {importResult.imported} schemas</li>
                    <li class="text-yellow-600 dark:text-yellow-400">⚠ Skipped: {importResult.skipped} schemas</li>
                    {#if importResult.errors.length > 0}
                      <li class="text-red-600 dark:text-red-400">✗ Errors:</li>
                      <ul class="ml-4 space-y-1">
                        {#each importResult.errors as error}
                          <li class="text-red-600 dark:text-red-400">• {error}</li>
                        {/each}
                      </ul>
                    {/if}
                  </ul>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}