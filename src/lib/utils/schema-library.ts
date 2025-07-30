/**
 * Schema Library Management System
 * Provides centralized management of reusable structured output schemas
 */

export interface SchemaLibraryItem {
  id: string;
  name: string;
  description: string;
  schema: string;
  category: 'built-in' | 'user' | 'imported';
  tags: string[];
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  author?: string;
  usage_count?: number;
}

export interface SchemaLibrary {
  version: string;
  schemas: SchemaLibraryItem[];
  lastUpdated: string;
}

const LIBRARY_STORAGE_KEY = 'structured-output-schema-library';
const LIBRARY_VERSION = '1.0.0';

/**
 * Get all schemas from the library
 */
export const getSchemaLibrary = (): SchemaLibrary => {
  try {
    const stored = localStorage.getItem(LIBRARY_STORAGE_KEY);
    if (stored) {
      const library = JSON.parse(stored) as SchemaLibrary;
      // Ensure built-in schemas are always present
      return ensureBuiltInSchemas(library);
    }
  } catch (error) {
    console.warn('Failed to load schema library from localStorage:', error);
  }
  
  // Return default library with built-in schemas
  return createDefaultLibrary();
};

/**
 * Save the schema library to localStorage
 */
export const saveSchemaLibrary = (library: SchemaLibrary): void => {
  try {
    library.lastUpdated = new Date().toISOString();
    localStorage.setItem(LIBRARY_STORAGE_KEY, JSON.stringify(library));
  } catch (error) {
    console.error('Failed to save schema library to localStorage:', error);
    throw new Error('Failed to save schema library');
  }
};

/**
 * Add a new schema to the library
 */
export const addSchemaToLibrary = (
  name: string,
  description: string,
  schema: string,
  options: {
    tags?: string[];
    isPublic?: boolean;
    author?: string;
  } = {}
): SchemaLibraryItem => {
  const library = getSchemaLibrary();
  
  const newSchema: SchemaLibraryItem = {
    id: generateSchemaId(),
    name,
    description,
    schema,
    category: 'user',
    tags: options.tags || [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isPublic: options.isPublic || false,
    author: options.author,
    usage_count: 0
  };
  
  library.schemas.push(newSchema);
  saveSchemaLibrary(library);
  
  return newSchema;
};

/**
 * Update an existing schema in the library
 */
export const updateSchemaInLibrary = (
  id: string,
  updates: Partial<Pick<SchemaLibraryItem, 'name' | 'description' | 'schema' | 'tags' | 'isPublic'>>
): SchemaLibraryItem | null => {
  const library = getSchemaLibrary();
  const schemaIndex = library.schemas.findIndex(s => s.id === id);
  
  if (schemaIndex === -1) {
    return null;
  }
  
  // Don't allow updating built-in schemas
  if (library.schemas[schemaIndex].category === 'built-in') {
    throw new Error('Cannot update built-in schemas');
  }
  
  library.schemas[schemaIndex] = {
    ...library.schemas[schemaIndex],
    ...updates,
    updatedAt: new Date().toISOString()
  };
  
  saveSchemaLibrary(library);
  return library.schemas[schemaIndex];
};

/**
 * Delete a schema from the library
 */
export const deleteSchemaFromLibrary = (id: string): boolean => {
  const library = getSchemaLibrary();
  const schemaIndex = library.schemas.findIndex(s => s.id === id);
  
  if (schemaIndex === -1) {
    return false;
  }
  
  // Don't allow deleting built-in schemas
  if (library.schemas[schemaIndex].category === 'built-in') {
    throw new Error('Cannot delete built-in schemas');
  }
  
  library.schemas.splice(schemaIndex, 1);
  saveSchemaLibrary(library);
  
  return true;
};

/**
 * Get a specific schema by ID
 */
export const getSchemaById = (id: string): SchemaLibraryItem | null => {
  const library = getSchemaLibrary();
  return library.schemas.find(s => s.id === id) || null;
};

/**
 * Search schemas by name, description, or tags
 */
export const searchSchemas = (query: string, category?: SchemaLibraryItem['category']): SchemaLibraryItem[] => {
  const library = getSchemaLibrary();
  const lowercaseQuery = query.toLowerCase();
  
  return library.schemas.filter(schema => {
    if (category && schema.category !== category) {
      return false;
    }
    
    return (
      schema.name.toLowerCase().includes(lowercaseQuery) ||
      schema.description.toLowerCase().includes(lowercaseQuery) ||
      schema.tags.some(tag => tag.toLowerCase().includes(lowercaseQuery))
    );
  });
};

/**
 * Increment usage count for a schema
 */
export const incrementSchemaUsage = (id: string): void => {
  const library = getSchemaLibrary();
  const schema = library.schemas.find(s => s.id === id);
  
  if (schema) {
    schema.usage_count = (schema.usage_count || 0) + 1;
    schema.updatedAt = new Date().toISOString();
    saveSchemaLibrary(library);
  }
};

/**
 * Export schemas to JSON
 */
export const exportSchemasToJSON = (schemaIds?: string[]): string => {
  const library = getSchemaLibrary();
  const schemasToExport = schemaIds 
    ? library.schemas.filter(s => schemaIds.includes(s.id))
    : library.schemas.filter(s => s.category === 'user');
    
  const exportData = {
    version: LIBRARY_VERSION,
    exportedAt: new Date().toISOString(),
    schemas: schemasToExport
  };
  
  return JSON.stringify(exportData, null, 2);
};

/**
 * Import schemas from JSON
 */
export const importSchemasFromJSON = (jsonData: string): { imported: number; skipped: number; errors: string[] } => {
  const library = getSchemaLibrary();
  const errors: string[] = [];
  let imported = 0;
  let skipped = 0;
  
  try {
    const importData = JSON.parse(jsonData);
    
    if (!importData.schemas || !Array.isArray(importData.schemas)) {
      throw new Error('Invalid import format: missing schemas array');
    }
    
    for (const schemaData of importData.schemas) {
      try {
        // Validate required fields
        if (!schemaData.name || !schemaData.schema) {
          errors.push(`Skipped schema: missing required fields (name or schema)`);
          skipped++;
          continue;
        }
        
        // Check if schema already exists (by name)
        const existingSchema = library.schemas.find(s => s.name === schemaData.name);
        if (existingSchema) {
          errors.push(`Skipped schema "${schemaData.name}": already exists`);
          skipped++;
          continue;
        }
        
        // Create new schema with imported category
        const newSchema: SchemaLibraryItem = {
          id: generateSchemaId(),
          name: schemaData.name,
          description: schemaData.description || '',
          schema: schemaData.schema,
          category: 'imported',
          tags: schemaData.tags || [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          isPublic: false, // Imported schemas are private by default
          author: schemaData.author,
          usage_count: 0
        };
        
        library.schemas.push(newSchema);
        imported++;
        
      } catch (error) {
        errors.push(`Failed to import schema: ${error.message}`);
        skipped++;
      }
    }
    
    if (imported > 0) {
      saveSchemaLibrary(library);
    }
    
  } catch (error) {
    errors.push(`Failed to parse import data: ${error.message}`);
  }
  
  return { imported, skipped, errors };
};

/**
 * Generate a unique schema ID
 */
const generateSchemaId = (): string => {
  return `schema_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Create default library with built-in schemas
 */
const createDefaultLibrary = (): SchemaLibrary => {
  const builtInSchemas: SchemaLibraryItem[] = [
    {
      id: 'builtin_simple',
      name: 'Simple Object',
      description: 'Basic result with confidence score',
      schema: JSON.stringify({
        type: "object",
        properties: {
          result: { type: "string" },
          confidence: { type: "number", minimum: 0, maximum: 1 }
        },
        required: ["result"]
      }, null, 2),
      category: 'built-in',
      tags: ['basic', 'simple'],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isPublic: true,
      author: 'System',
      usage_count: 0
    },
    {
      id: 'builtin_checklist',
      name: 'Checklist Item',
      description: 'Task with completion status and priority',
      schema: JSON.stringify({
        type: "object",
        properties: {
          task: { type: "string" },
          completed: { type: "boolean" },
          notes: { type: "string" },
          priority: { type: "string", enum: ["low", "medium", "high"] }
        },
        required: ["task", "completed"]
      }, null, 2),
      category: 'built-in',
      tags: ['task', 'checklist', 'todo'],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isPublic: true,
      author: 'System',
      usage_count: 0
    },
    {
      id: 'builtin_analysis',
      name: 'Analysis Result',
      description: 'Comprehensive analysis with summary, key points, and recommendations',
      schema: JSON.stringify({
        type: "object",
        properties: {
          summary: { type: "string" },
          key_points: {
            type: "array",
            items: { type: "string" }
          },
          score: { type: "integer", minimum: 1, maximum: 10 },
          recommendations: {
            type: "array",
            items: { type: "string" }
          }
        },
        required: ["summary", "score"]
      }, null, 2),
      category: 'built-in',
      tags: ['analysis', 'evaluation', 'report'],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isPublic: true,
      author: 'System',
      usage_count: 0
    }
  ];
  
  return {
    version: LIBRARY_VERSION,
    schemas: builtInSchemas,
    lastUpdated: new Date().toISOString()
  };
};

/**
 * Ensure built-in schemas are present in the library
 */
const ensureBuiltInSchemas = (library: SchemaLibrary): SchemaLibrary => {
  const defaultLibrary = createDefaultLibrary();
  
  // Add any missing built-in schemas
  for (const builtInSchema of defaultLibrary.schemas) {
    const exists = library.schemas.some(s => s.id === builtInSchema.id);
    if (!exists) {
      library.schemas.unshift(builtInSchema); // Add to beginning
    }
  }
  
  return library;
};

/**
 * Get popular schemas (by usage count)
 */
export const getPopularSchemas = (limit: number = 5): SchemaLibraryItem[] => {
  const library = getSchemaLibrary();
  return library.schemas
    .filter(s => s.usage_count && s.usage_count > 0)
    .sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
    .slice(0, limit);
};

/**
 * Get recently used schemas
 */
export const getRecentSchemas = (limit: number = 5): SchemaLibraryItem[] => {
  const library = getSchemaLibrary();
  return library.schemas
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, limit);
};