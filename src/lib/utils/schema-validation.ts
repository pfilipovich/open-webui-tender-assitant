export interface SchemaValidationResult {
  valid: boolean;
  error?: string;
  warnings?: string[];
  schema?: object;
  stats?: {
    totalProperties: number;
    maxNestingDepth: number;
    totalStringLength: number;
    enumCount: number;
  };
}

export interface OpenAIValidationLimits {
  maxProperties: number;
  maxNestingDepth: number;
  maxStringLength: number;
  maxEnumValues: number;
  maxEnumStringLength: number;
}

export const OPENAI_LIMITS: OpenAIValidationLimits = {
  maxProperties: 5000,
  maxNestingDepth: 5,
  maxStringLength: 120000,
  maxEnumValues: 1000,
  maxEnumStringLength: 15000
};

// Helper function to count total properties in a schema
const countProperties = (schema: any, visited = new Set()): number => {
  if (!schema || typeof schema !== 'object' || visited.has(schema)) {
    return 0;
  }
  
  visited.add(schema);
  let count = 0;
  
  if (schema.properties && typeof schema.properties === 'object') {
    count += Object.keys(schema.properties).length;
    for (const prop of Object.values(schema.properties)) {
      count += countProperties(prop, visited);
    }
  }
  
  if (schema.items) {
    count += countProperties(schema.items, visited);
  }
  
  if (schema.additionalProperties && typeof schema.additionalProperties === 'object') {
    count += countProperties(schema.additionalProperties, visited);
  }
  
  return count;
};

// Helper function to calculate maximum nesting depth
const calculateNestingDepth = (schema: any, currentDepth = 0, visited = new Set()): number => {
  if (!schema || typeof schema !== 'object' || visited.has(schema)) {
    return currentDepth;
  }
  
  visited.add(schema);
  let maxDepth = currentDepth;
  
  if (schema.properties && typeof schema.properties === 'object') {
    for (const prop of Object.values(schema.properties)) {
      const depth = calculateNestingDepth(prop, currentDepth + 1, visited);
      maxDepth = Math.max(maxDepth, depth);
    }
  }
  
  if (schema.items) {
    const depth = calculateNestingDepth(schema.items, currentDepth + 1, visited);
    maxDepth = Math.max(maxDepth, depth);
  }
  
  return maxDepth;
};

// Helper function to calculate total string length
const calculateStringLength = (obj: any, visited = new Set()): number => {
  if (visited.has(obj)) return 0;
  visited.add(obj);
  
  let totalLength = 0;
  
  if (typeof obj === 'string') {
    totalLength += obj.length;
  } else if (Array.isArray(obj)) {
    for (const item of obj) {
      totalLength += calculateStringLength(item, visited);
    }
  } else if (obj && typeof obj === 'object') {
    for (const [key, value] of Object.entries(obj)) {
      totalLength += key.length; // Property names count toward limit
      totalLength += calculateStringLength(value, visited);
    }
  }
  
  return totalLength;
};

// Helper function to count enum values
const countEnumValues = (schema: any, visited = new Set()): { count: number; totalStringLength: number } => {
  if (!schema || typeof schema !== 'object' || visited.has(schema)) {
    return { count: 0, totalStringLength: 0 };
  }
  
  visited.add(schema);
  let count = 0;
  let totalStringLength = 0;
  
  if (schema.enum && Array.isArray(schema.enum)) {
    count += schema.enum.length;
    totalStringLength += calculateStringLength(schema.enum);
  }
  
  if (schema.properties && typeof schema.properties === 'object') {
    for (const prop of Object.values(schema.properties)) {
      const { count: propCount, totalStringLength: propStringLength } = countEnumValues(prop, visited);
      count += propCount;
      totalStringLength += propStringLength;
    }
  }
  
  if (schema.items) {
    const { count: itemsCount, totalStringLength: itemsStringLength } = countEnumValues(schema.items, visited);
    count += itemsCount;
    totalStringLength += itemsStringLength;
  }
  
  return { count, totalStringLength };
};

export const validateJsonSchema = (
  schemaStr: string, 
  options: { 
    enableOpenAIValidation?: boolean;
    strictMode?: boolean;
  } = {}
): SchemaValidationResult => {
  const { enableOpenAIValidation = true, strictMode = false } = options;
  
  if (!schemaStr.trim()) {
    return { valid: true };
  }

  try {
    const schema = JSON.parse(schemaStr);
    
    if (typeof schema !== 'object' || schema === null) {
      return { valid: false, error: 'Schema must be a JSON object' };
    }
    
    if (!schema.type) {
      return { valid: false, error: 'Schema must have a "type" field' };
    }
    
    // Basic validation passed, now perform enhanced validation
    const warnings: string[] = [];
    const errors: string[] = [];
    
    if (enableOpenAIValidation) {
      // Calculate schema statistics
      const totalProperties = countProperties(schema);
      const maxNestingDepth = calculateNestingDepth(schema);
      const totalStringLength = calculateStringLength(schema);
      const { count: enumCount, totalStringLength: enumStringLength } = countEnumValues(schema);
      
      const stats = {
        totalProperties,
        maxNestingDepth,
        totalStringLength,
        enumCount
      };
      
      // OpenAI-specific validation checks
      if (totalProperties > OPENAI_LIMITS.maxProperties) {
        const message = `Schema has ${totalProperties} properties, but OpenAI supports max ${OPENAI_LIMITS.maxProperties}`;
        if (strictMode) {
          errors.push(message);
        } else {
          warnings.push(message);
        }
      }
      
      if (maxNestingDepth > OPENAI_LIMITS.maxNestingDepth) {
        const message = `Schema nesting depth is ${maxNestingDepth}, but OpenAI supports max ${OPENAI_LIMITS.maxNestingDepth} levels`;
        if (strictMode) {
          errors.push(message);
        } else {
          warnings.push(message);
        }
      }
      
      if (totalStringLength > OPENAI_LIMITS.maxStringLength) {
        const message = `Total string length is ${totalStringLength} characters, but OpenAI supports max ${OPENAI_LIMITS.maxStringLength}`;
        if (strictMode) {
          errors.push(message);
        } else {
          warnings.push(message);
        }
      }
      
      if (enumCount > OPENAI_LIMITS.maxEnumValues) {
        const message = `Schema has ${enumCount} enum values, but OpenAI supports max ${OPENAI_LIMITS.maxEnumValues}`;
        if (strictMode) {
          errors.push(message);
        } else {
          warnings.push(message);
        }
      }
      
      if (enumStringLength > OPENAI_LIMITS.maxEnumStringLength) {
        const message = `Enum string length is ${enumStringLength} characters, but for large enums OpenAI supports max ${OPENAI_LIMITS.maxEnumStringLength}`;
        warnings.push(message);
      }
      
      // Check for unsupported features
      if (hasUnsupportedFeatures(schema)) {
        warnings.push('Schema contains features that may not be fully supported by OpenAI structured output (e.g., anyOf at root level, complex conditionals)');
      }
      
      // Provide helpful warnings for approaching limits
      if (totalProperties > OPENAI_LIMITS.maxProperties * 0.8) {
        warnings.push(`Schema is approaching the property limit (${totalProperties}/${OPENAI_LIMITS.maxProperties}). Consider simplifying.`);
      }
      
      if (totalStringLength > OPENAI_LIMITS.maxStringLength * 0.8) {
        warnings.push(`Schema is approaching the string length limit (${totalStringLength}/${OPENAI_LIMITS.maxStringLength}). Consider shorter names.`);
      }
      
      return {
        valid: errors.length === 0,
        error: errors.length > 0 ? errors[0] : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
        schema,
        stats
      };
    }
    
    return { valid: true, schema };
  } catch (e) {
    return { valid: false, error: 'Invalid JSON format' };
  }
};

// Helper function to detect unsupported OpenAI features
const hasUnsupportedFeatures = (schema: any, visited = new Set()): boolean => {
  if (!schema || typeof schema !== 'object' || visited.has(schema)) {
    return false;
  }
  
  visited.add(schema);
  
  // Check for root-level anyOf (not supported)
  if (schema.anyOf && !schema.properties) {
    return true;
  }
  
  // Check for complex conditionals
  if (schema.if && schema.then && schema.else) {
    return true;
  }
  
  // Check for pattern properties
  if (schema.patternProperties) {
    return true;
  }
  
  // Check for $ref
  if (schema.$ref) {
    return true;
  }
  
  // Recursively check nested schemas
  if (schema.properties && typeof schema.properties === 'object') {
    for (const prop of Object.values(schema.properties)) {
      if (hasUnsupportedFeatures(prop, visited)) {
        return true;
      }
    }
  }
  
  if (schema.items && hasUnsupportedFeatures(schema.items, visited)) {
    return true;
  }
  
  return false;
};

export const getSchemaTemplates = () => ({
  simple: {
    name: "Simple Object",
    description: "Basic result with confidence score",
    schema: JSON.stringify({
      type: "object",
      properties: {
        result: { type: "string" },
        confidence: { type: "number", minimum: 0, maximum: 1 }
      },
      required: ["result"]
    }, null, 2)
  },
  checklist: {
    name: "Checklist Item", 
    description: "Task with completion status",
    schema: JSON.stringify({
      type: "object",
      properties: {
        task: { type: "string" },
        completed: { type: "boolean" },
        notes: { type: "string" },
        priority: { type: "string", enum: ["low", "medium", "high"] }
      },
      required: ["task", "completed"]
    }, null, 2)
  },
  analysis: {
    name: "Analysis Result",
    description: "Summary with key points and score",
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
    }, null, 2)
  }
});