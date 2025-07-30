/**
 * Event Protection Utilities for Structured Output
 * 
 * This module provides utilities to prevent event listener conflicts and race conditions
 * during structured output operations, particularly in modal interactions.
 */

// Global state lock to prevent listener conflicts
declare global {
    interface Window {
        __structuredOutputInProgress?: boolean;
        __structuredOutputDebug?: boolean;
    }
}

/**
 * Enhanced event listener with priority and isolation
 * Prevents event conflicts during structured output operations
 */
export const addProtectedEventListener = (
    element: Element | Window | Document,
    event: string,
    handler: (e: Event) => void,
    options: AddEventListenerOptions = {}
): void => {
    const protectedHandler = (e: Event) => {
        // Check if structured output operation is in progress
        if (window.__structuredOutputInProgress) {
            if (window.__structuredOutputDebug) {
                console.log(`🛡️ Event blocked during structured output operation: ${event}`);
            }
            e.stopImmediatePropagation();
            return;
        }
        
        // Call original handler
        handler(e);
    };
    
    // Add event listener with capture priority
    element.addEventListener(event, protectedHandler, {
        ...options,
        capture: true // Ensure priority over other listeners
    });
};

/**
 * State locking during critical operations
 * Prevents interference from global event handlers
 */
export const withStateLock = async <T>(operation: () => Promise<T> | T): Promise<T> => {
    const wasLocked = window.__structuredOutputInProgress;
    
    try {
        window.__structuredOutputInProgress = true;
        
        if (window.__structuredOutputDebug) {
            console.log('🔒 State lock acquired');
        }
        
        const result = await Promise.resolve(operation());
        return result;
        
    } finally {
        // Only release lock if we acquired it
        if (!wasLocked) {
            window.__structuredOutputInProgress = false;
            
            if (window.__structuredOutputDebug) {
                console.log('🔓 State lock released');
            }
        }
    }
};

/**
 * Synchronous state locking for immediate operations
 */
export const withStateLockSync = <T>(operation: () => T): T => {
    const wasLocked = window.__structuredOutputInProgress;
    
    try {
        window.__structuredOutputInProgress = true;
        
        if (window.__structuredOutputDebug) {
            console.log('🔒 Sync state lock acquired');
        }
        
        return operation();
        
    } finally {
        // Only release lock if we acquired it
        if (!wasLocked) {
            window.__structuredOutputInProgress = false;
            
            if (window.__structuredOutputDebug) {
                console.log('🔓 Sync state lock released');
            }
        }
    }
};

/**
 * Check if structured output operation is currently in progress
 */
export const isStateLocked = (): boolean => {
    return Boolean(window.__structuredOutputInProgress);
};

/**
 * Force release state lock (use with caution)
 */
export const forceReleaseStateLock = (): void => {
    const wasLocked = window.__structuredOutputInProgress;
    window.__structuredOutputInProgress = false;
    
    if (window.__structuredOutputDebug && wasLocked) {
        console.warn('⚠️ State lock force released');
    }
};

/**
 * Enable debug logging for event protection
 */
export const enableEventProtectionDebug = (enabled: boolean = true): void => {
    window.__structuredOutputDebug = enabled;
    console.log(`🐛 Event protection debug ${enabled ? 'enabled' : 'disabled'}`);
};

/**
 * Create a protected event handler that respects state locks
 */
export const createProtectedHandler = <T extends Event>(
    handler: (e: T) => void,
    allowDuringLock: boolean = false
) => {
    return (e: T) => {
        if (!allowDuringLock && window.__structuredOutputInProgress) {
            if (window.__structuredOutputDebug) {
                console.log(`🛡️ Handler blocked during structured output operation`);
            }
            e.stopImmediatePropagation();
            return;
        }
        
        handler(e);
    };
};

/**
 * Modal-specific event protection
 * Creates an event boundary around modal elements
 */
export const createModalEventBoundary = (modalElement: HTMLElement): (() => void) => {
    const eventTypes = ['keydown', 'keyup', 'click', 'focus', 'blur', 'mousedown', 'mouseup'];
    const handlers: Array<[string, (e: Event) => void]> = [];
    
    // Interactive elements that should be allowed to handle events normally
    const isInteractiveElement = (element: Element): boolean => {
        const tagName = element.tagName.toLowerCase();
        const interactiveTags = ['button', 'input', 'select', 'textarea', 'a'];
        
        // Check if it's an interactive tag
        if (interactiveTags.includes(tagName)) {
            return true;
        }
        
        // Check for interactive attributes
        if (element.hasAttribute('onclick') || 
            element.hasAttribute('role') && ['button', 'link', 'menuitem'].includes(element.getAttribute('role'))) {
            return true;
        }
        
        // Check for clickable class patterns (common in UI frameworks)
        const className = element.className;
        if (typeof className === 'string' && 
            (className.includes('btn') || className.includes('button') || className.includes('clickable'))) {
            return true;
        }
        
        return false;
    };
    
    // Find the closest interactive element in the target chain
    const findInteractiveParent = (element: Element): Element | null => {
        let current = element;
        while (current && current !== modalElement) {
            if (isInteractiveElement(current)) {
                return current;
            }
            current = current.parentElement;
        }
        return null;
    };
    
    eventTypes.forEach(eventType => {
        const handler = (e: Event) => {
            const target = e.target as Element;
            
            if (!target) return;
            
            // Allow events on interactive elements to proceed normally
            const interactiveParent = findInteractiveParent(target);
            if (interactiveParent) {
                if (window.__structuredOutputDebug) {
                    console.log(`✅ Modal boundary allowed: ${eventType} on interactive element`, interactiveParent.tagName);
                }
                return; // Don't stop propagation for interactive elements
            }
            
            // Only stop propagation for non-interactive elements to prevent global interference
            e.stopPropagation();
            
            if (window.__structuredOutputDebug) {
                console.log(`🚧 Modal boundary captured: ${eventType} on non-interactive element`, target.tagName);
            }
        };
        
        modalElement.addEventListener(eventType, handler, { capture: true });
        handlers.push([eventType, handler]);
    });
    
    // Return cleanup function
    return () => {
        handlers.forEach(([eventType, handler]) => {
            modalElement.removeEventListener(eventType, handler, { capture: true });
        });
        
        if (window.__structuredOutputDebug) {
            console.log('🧹 Modal event boundary cleaned up');
        }
    };
};

/**
 * Enhanced keyboard event protection
 * Provides specific protection for common keyboard shortcuts
 */
export const protectKeyboardShortcuts = (element: Element | Window = window): (() => void) => {
    const shortcuts = ['Escape', 'Enter', 'Tab', 'Space'];
    const handlers: Array<[string, (e: Event) => void]> = [];
    
    const keydownHandler = (e: KeyboardEvent) => {
        if (window.__structuredOutputInProgress && shortcuts.includes(e.key)) {
            if (window.__structuredOutputDebug) {
                console.log(`⌨️ Keyboard shortcut blocked: ${e.key}`);
            }
            e.stopImmediatePropagation();
            e.preventDefault();
        }
    };
    
    element.addEventListener('keydown', keydownHandler, { capture: true });
    handlers.push(['keydown', keydownHandler]);
    
    // Return cleanup function
    return () => {
        handlers.forEach(([eventType, handler]) => {
            element.removeEventListener(eventType, handler, { capture: true });
        });
    };
};

/**
 * Debounced state operations to prevent rapid state changes
 */
export const debounceStateOperation = <T extends any[]>(
    operation: (...args: T) => void,
    delay: number = 100
): ((...args: T) => void) => {
    let timeoutId: number | null = null;
    
    return (...args: T) => {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
        
        timeoutId = window.setTimeout(() => {
            if (!window.__structuredOutputInProgress) {
                operation(...args);
            } else if (window.__structuredOutputDebug) {
                console.log('⏱️ Debounced operation skipped due to state lock');
            }
            timeoutId = null;
        }, delay);
    };
};

/**
 * Safe modal operation wrapper
 * Ensures modal operations don't conflict with global state
 */
export const safeModalOperation = async <T>(
    modalElement: HTMLElement,
    operation: () => Promise<T> | T
): Promise<T> => {
    const cleanupBoundary = createModalEventBoundary(modalElement);
    
    try {
        return await withStateLock(operation);
    } finally {
        cleanupBoundary();
    }
};

/**
 * Initialize event protection system
 * Call this once during application startup
 */
export const initializeEventProtection = (debug: boolean = false): void => {
    // Enable debug mode if requested
    if (debug) {
        enableEventProtectionDebug(true);
    }
    
    // Set up global error handler for uncaught state lock issues
    window.addEventListener('error', (e) => {
        if (e.error?.message?.includes('structured output')) {
            console.error('🚨 Structured output error detected, releasing state lock', e.error);
            forceReleaseStateLock();
        }
    });
    
    // Clean up state lock on page unload
    window.addEventListener('beforeunload', () => {
        forceReleaseStateLock();
    });
    
    if (window.__structuredOutputDebug) {
        console.log('🚀 Event protection system initialized');
    }
};

// Type definitions for better TypeScript support
export interface ProtectedEventListenerOptions extends AddEventListenerOptions {
    allowDuringLock?: boolean;
}

export interface StateOperationOptions {
    timeout?: number;
    retryOnLock?: boolean;
    maxRetries?: number;
}

/**
 * Advanced state operation with retry logic
 */
export const safeStateOperation = async <T>(
    operation: () => Promise<T> | T,
    options: StateOperationOptions = {}
): Promise<T> => {
    const {
        timeout = 5000,
        retryOnLock = true,
        maxRetries = 3
    } = options;
    
    let retries = 0;
    
    while (retries <= maxRetries) {
        try {
            // Check if we can proceed
            if (window.__structuredOutputInProgress && !retryOnLock) {
                throw new Error('Cannot perform operation while structured output is in progress');
            }
            
            // If locked and retry is enabled, wait briefly
            if (window.__structuredOutputInProgress && retryOnLock) {
                if (retries < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, 100 * (retries + 1)));
                    retries++;
                    continue;
                }
                throw new Error('Max retries exceeded waiting for state lock release');
            }
            
            // Perform operation with timeout
            return await Promise.race([
                Promise.resolve(operation()),
                new Promise<never>((_, reject) => 
                    setTimeout(() => reject(new Error('Operation timeout')), timeout)
                )
            ]);
            
        } catch (error) {
            if (retries < maxRetries && retryOnLock) {
                retries++;
                if (window.__structuredOutputDebug) {
                    console.log(`🔄 Retrying operation (attempt ${retries}/${maxRetries})`);
                }
                continue;
            }
            throw error;
        }
    }
    
    throw new Error('Unexpected end of retry loop');
};

// Enhanced State Validation Types and Functions
export interface StructuredOutputState {
    structuredOutput?: boolean;
    structuredOutputSchema?: string;
    structuredOutputName?: string;
    attachedPrompt?: any;
}

export interface StateValidationResult {
    consistent: boolean;
    inconsistencies: string[];
    capturedState: StructuredOutputState;
    currentState: StructuredOutputState;
    recommendation: 'use_captured' | 'use_current' | 'prompt_user';
}

export interface StateValidationOptions {
    tolerateMinorChanges?: boolean;
    logInconsistencies?: boolean;
    autoResolve?: boolean;
}

/**
 * Enhanced state validation for structured output operations
 * Compares captured state with current state to detect inconsistencies
 */
export const validateStructuredOutputState = (
    capturedState: StructuredOutputState,
    currentState: StructuredOutputState,
    options: StateValidationOptions = {}
): StateValidationResult => {
    const {
        tolerateMinorChanges = true,
        logInconsistencies = true,
        autoResolve = true
    } = options;
    
    const inconsistencies: string[] = [];
    
    // Check each critical field for inconsistencies
    const fieldsToCheck = [
        'structuredOutput',
        'structuredOutputSchema', 
        'structuredOutputName'
    ];
    
    fieldsToCheck.forEach(field => {
        const capturedValue = capturedState[field];
        const currentValue = currentState[field];
        
        // Compare values (handle null/undefined/empty string as equivalent for names)
        const normalizedCaptured = field.includes('Name') ? 
            (capturedValue || '') : capturedValue;
        const normalizedCurrent = field.includes('Name') ? 
            (currentValue || '') : currentValue;
            
        if (JSON.stringify(normalizedCaptured) !== JSON.stringify(normalizedCurrent)) {
            inconsistencies.push(`${field}: captured="${normalizedCaptured}" vs current="${normalizedCurrent}"`);
        }
    });
    
    // Special handling for attached prompt (compare by id or title)
    if (capturedState.attachedPrompt || currentState.attachedPrompt) {
        const capturedPromptId = capturedState.attachedPrompt?.id || capturedState.attachedPrompt?.title;
        const currentPromptId = currentState.attachedPrompt?.id || currentState.attachedPrompt?.title;
        
        if (capturedPromptId !== currentPromptId) {
            inconsistencies.push(`attachedPrompt: captured="${capturedPromptId}" vs current="${currentPromptId}"`);
        }
    }
    
    const consistent = inconsistencies.length === 0;
    
    // Determine recommendation based on inconsistencies
    let recommendation: 'use_captured' | 'use_current' | 'prompt_user' = 'use_captured';
    
    if (!consistent) {
        if (autoResolve && tolerateMinorChanges && inconsistencies.length <= 2) {
            // Minor changes - prefer captured state (more stable)
            recommendation = 'use_captured';
        } else if (inconsistencies.length > 2) {
            // Major changes - may need user input
            recommendation = 'prompt_user';
        } else {
            // Default to captured state for consistency
            recommendation = 'use_captured';
        }
    }
    
    // Log inconsistencies if enabled
    if (logInconsistencies && !consistent && window.__structuredOutputDebug) {
        console.warn('🔍 State inconsistency detected:', {
            inconsistencies,
            capturedState,
            currentState,
            recommendation
        });
    }
    
    return {
        consistent,
        inconsistencies,
        capturedState,
        currentState,
        recommendation
    };
};

/**
 * Enhanced state capture with validation
 * Captures current state and validates against previous capture if provided
 */
export const captureStructuredOutputState = (
    getCurrentState: () => StructuredOutputState,
    previousCapture?: StructuredOutputState,
    options: StateValidationOptions = {}
): { state: StructuredOutputState; validation?: StateValidationResult } => {
    const currentState = getCurrentState();
    
    if (window.__structuredOutputDebug) {
        console.log('📸 Capturing structured output state:', currentState);
    }
    
    // If we have a previous capture, validate consistency
    let validation: StateValidationResult | undefined;
    if (previousCapture) {
        validation = validateStructuredOutputState(previousCapture, currentState, options);
    }
    
    return {
        state: currentState,
        validation
    };
};

/**
 * Safe state operation with enhanced validation
 * Wraps state-sensitive operations with capture, validation, and consistency checks
 */
export const withStateValidation = async <T>(
    operation: (validatedState: StructuredOutputState) => Promise<T> | T,
    getCurrentState: () => StructuredOutputState,
    options: StateValidationOptions & { 
        onInconsistency?: (validation: StateValidationResult) => StructuredOutputState | Promise<StructuredOutputState>;
    } = {}
): Promise<T> => {
    const { onInconsistency, ...validationOptions } = options;
    
    return await withStateLock(async () => {
        // Capture initial state
        const { state: initialState } = captureStructuredOutputState(getCurrentState, undefined, validationOptions);
        
        // Capture state again after a brief delay to check for changes
        await new Promise(resolve => setTimeout(resolve, 10));
        const { state: finalState, validation } = captureStructuredOutputState(
            getCurrentState, 
            initialState, 
            validationOptions
        );
        
        let operationState = finalState;
        
        // Handle inconsistencies
        if (validation && !validation.consistent) {
            if (onInconsistency) {
                operationState = await onInconsistency(validation);
            } else {
                // Default behavior: use captured state based on recommendation
                operationState = validation.recommendation === 'use_current' ? 
                    validation.currentState : validation.capturedState;
            }
        }
        
        return await Promise.resolve(operation(operationState));
    });
};

/**
 * Reactive state monitor for detecting rapid changes
 * Helps identify potential race conditions in real-time
 */
export const createStateMonitor = (
    getCurrentState: () => StructuredOutputState,
    onStateChange: (newState: StructuredOutputState, previousState: StructuredOutputState) => void,
    interval: number = 100
): (() => void) => {
    let previousState = getCurrentState();
    let monitoring = true;
    
    const monitor = () => {
        if (!monitoring) return;
        
        const currentState = getCurrentState();
        const validation = validateStructuredOutputState(previousState, currentState, {
            logInconsistencies: false
        });
        
        if (!validation.consistent) {
            onStateChange(currentState, previousState);
            previousState = currentState;
        }
        
        setTimeout(monitor, interval);
    };
    
    // Start monitoring
    setTimeout(monitor, interval);
    
    // Return cleanup function
    return () => {
        monitoring = false;
    };
};