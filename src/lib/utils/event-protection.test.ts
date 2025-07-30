/**
 * Unit tests for event protection utilities
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
    addProtectedEventListener,
    withStateLock,
    withStateLockSync,
    isStateLocked,
    forceReleaseStateLock,
    enableEventProtectionDebug,
    createProtectedHandler,
    createModalEventBoundary,
    protectKeyboardShortcuts,
    debounceStateOperation,
    safeModalOperation,
    initializeEventProtection,
    safeStateOperation
} from './event-protection';

// Mock DOM and window objects
const mockElement = {
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
};

const mockWindow = {
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    setTimeout: vi.fn((cb, delay) => {
        // Immediately execute for testing
        setTimeout(cb, 0);
        return 123;
    }),
    clearTimeout: vi.fn()
};

// Setup global window mock
beforeEach(() => {
    // Reset global state
    delete (window as any).__structuredOutputInProgress;
    delete (window as any).__structuredOutputDebug;
    
    // Clear all mocks
    vi.clearAllMocks();
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
    // Clean up global state
    forceReleaseStateLock();
    vi.restoreAllMocks();
});

describe('Event Protection Utilities', () => {
    
    describe('addProtectedEventListener', () => {
        it('should add event listener normally when no state lock', () => {
            const handler = vi.fn();
            const element = mockElement as any;
            
            addProtectedEventListener(element, 'click', handler);
            
            expect(element.addEventListener).toHaveBeenCalledWith(
                'click',
                expect.any(Function),
                { capture: true }
            );
        });
        
        it('should block events when state is locked', () => {
            const handler = vi.fn();
            const element = mockElement as any;
            
            // Lock state
            (window as any).__structuredOutputInProgress = true;
            
            addProtectedEventListener(element, 'click', handler);
            
            // Get the protected handler
            const protectedHandler = element.addEventListener.mock.calls[0][1];
            
            // Create mock event
            const mockEvent = {
                stopImmediatePropagation: vi.fn()
            };
            
            // Call protected handler
            protectedHandler(mockEvent);
            
            expect(mockEvent.stopImmediatePropagation).toHaveBeenCalled();
            expect(handler).not.toHaveBeenCalled();
        });
        
        it('should call handler when state is not locked', () => {
            const handler = vi.fn();
            const element = mockElement as any;
            
            addProtectedEventListener(element, 'click', handler);
            
            // Get the protected handler
            const protectedHandler = element.addEventListener.mock.calls[0][1];
            
            // Create mock event
            const mockEvent = {
                stopImmediatePropagation: vi.fn()
            };
            
            // Call protected handler
            protectedHandler(mockEvent);
            
            expect(handler).toHaveBeenCalledWith(mockEvent);
            expect(mockEvent.stopImmediatePropagation).not.toHaveBeenCalled();
        });
    });
    
    describe('withStateLock', () => {
        it('should acquire and release state lock', async () => {
            const operation = vi.fn().mockResolvedValue('result');
            
            expect(isStateLocked()).toBe(false);
            
            const result = await withStateLock(operation);
            
            expect(result).toBe('result');
            expect(operation).toHaveBeenCalled();
            expect(isStateLocked()).toBe(false);
        });
        
        it('should handle nested locks correctly', async () => {
            const innerOperation = vi.fn().mockResolvedValue('inner');
            const outerOperation = vi.fn().mockImplementation(async () => {
                return await withStateLock(innerOperation);
            });
            
            const result = await withStateLock(outerOperation);
            
            expect(result).toBe('inner');
            expect(outerOperation).toHaveBeenCalled();
            expect(innerOperation).toHaveBeenCalled();
            expect(isStateLocked()).toBe(false);
        });
        
        it('should release lock even if operation throws', async () => {
            const operation = vi.fn().mockRejectedValue(new Error('test error'));
            
            await expect(withStateLock(operation)).rejects.toThrow('test error');
            expect(isStateLocked()).toBe(false);
        });
    });
    
    describe('withStateLockSync', () => {
        it('should acquire and release state lock synchronously', () => {
            const operation = vi.fn().mockReturnValue('result');
            
            expect(isStateLocked()).toBe(false);
            
            const result = withStateLockSync(operation);
            
            expect(result).toBe('result');
            expect(operation).toHaveBeenCalled();
            expect(isStateLocked()).toBe(false);
        });
        
        it('should release lock even if operation throws', () => {
            const operation = vi.fn().mockImplementation(() => {
                throw new Error('test error');
            });
            
            expect(() => withStateLockSync(operation)).toThrow('test error');
            expect(isStateLocked()).toBe(false);
        });
    });
    
    describe('isStateLocked', () => {
        it('should return false when not locked', () => {
            expect(isStateLocked()).toBe(false);
        });
        
        it('should return true when locked', () => {
            (window as any).__structuredOutputInProgress = true;
            expect(isStateLocked()).toBe(true);
        });
    });
    
    describe('forceReleaseStateLock', () => {
        it('should force release state lock', () => {
            (window as any).__structuredOutputInProgress = true;
            expect(isStateLocked()).toBe(true);
            
            forceReleaseStateLock();
            
            expect(isStateLocked()).toBe(false);
        });
    });
    
    describe('enableEventProtectionDebug', () => {
        it('should enable debug mode', () => {
            enableEventProtectionDebug(true);
            expect((window as any).__structuredOutputDebug).toBe(true);
        });
        
        it('should disable debug mode', () => {
            enableEventProtectionDebug(false);
            expect((window as any).__structuredOutputDebug).toBe(false);
        });
    });
    
    describe('createProtectedHandler', () => {
        it('should call handler when not locked', () => {
            const handler = vi.fn();
            const protectedHandler = createProtectedHandler(handler);
            const mockEvent = { stopImmediatePropagation: vi.fn() } as any;
            
            protectedHandler(mockEvent);
            
            expect(handler).toHaveBeenCalledWith(mockEvent);
            expect(mockEvent.stopImmediatePropagation).not.toHaveBeenCalled();
        });
        
        it('should block handler when locked', () => {
            (window as any).__structuredOutputInProgress = true;
            
            const handler = vi.fn();
            const protectedHandler = createProtectedHandler(handler);
            const mockEvent = { stopImmediatePropagation: vi.fn() } as any;
            
            protectedHandler(mockEvent);
            
            expect(handler).not.toHaveBeenCalled();
            expect(mockEvent.stopImmediatePropagation).toHaveBeenCalled();
        });     
        
        it('should allow handler when locked but allowDuringLock is true', () => {
            (window as any).__structuredOutputInProgress = true;
            
            const handler = vi.fn();
            const protectedHandler = createProtectedHandler(handler, true);
            const mockEvent = { stopImmediatePropagation: vi.fn() } as any;
            
            protectedHandler(mockEvent);
            
            expect(handler).toHaveBeenCalledWith(mockEvent);
            expect(mockEvent.stopImmediatePropagation).not.toHaveBeenCalled();
        });
    });
    
    describe('createModalEventBoundary', () => {
        it('should create event boundary and return cleanup function', () => {
            const mockModalElement = {
                addEventListener: vi.fn(),
                removeEventListener: vi.fn()
            } as any;
            
            const cleanup = createModalEventBoundary(mockModalElement);
            
            // Should add event listeners for all event types
            expect(mockModalElement.addEventListener).toHaveBeenCalledTimes(7); // keydown, keyup, click, focus, blur, mousedown, mouseup
            
            // Call cleanup
            cleanup();
            
            // Should remove all event listeners
            expect(mockModalElement.removeEventListener).toHaveBeenCalledTimes(7);
        });
    });
    
    describe('protectKeyboardShortcuts', () => {
        it('should protect keyboard shortcuts and return cleanup function', () => {
            const mockElement = {
                addEventListener: vi.fn(),
                removeEventListener: vi.fn()
            } as any;
            
            const cleanup = protectKeyboardShortcuts(mockElement);
            
            expect(mockElement.addEventListener).toHaveBeenCalledWith(
                'keydown',
                expect.any(Function),
                { capture: true }
            );
            
            cleanup();
            
            expect(mockElement.removeEventListener).toHaveBeenCalledWith(
                'keydown',
                expect.any(Function),
                { capture: true }
            );
        });
    });
    
    describe('debounceStateOperation', () => {
        it('should debounce operations', (done) => {
            const operation = vi.fn();
            const debouncedOperation = debounceStateOperation(operation, 50);
            
            // Call multiple times rapidly
            debouncedOperation('arg1');
            debouncedOperation('arg2');
            debouncedOperation('arg3');
            
            // Should not be called immediately
            expect(operation).not.toHaveBeenCalled();
            
            // Wait for debounce
            setTimeout(() => {
                expect(operation).toHaveBeenCalledTimes(1);
                expect(operation).toHaveBeenCalledWith('arg3'); // Last call wins
                done();
            }, 100);
        });
        
        it('should skip operation when state is locked', (done) => {
            (window as any).__structuredOutputInProgress = true;
            
            const operation = vi.fn();
            const debouncedOperation = debounceStateOperation(operation, 50);
            
            debouncedOperation('arg1');
            
            setTimeout(() => {
                expect(operation).not.toHaveBeenCalled();
                done();
            }, 100);
        });
    });
    
    describe('safeModalOperation', () => {
        it('should perform modal operation with boundary protection', async () => {
            const mockModalElement = {
                addEventListener: vi.fn(),
                removeEventListener: vi.fn()
            } as any;
            
            const operation = vi.fn().mockResolvedValue('result');
            
            const result = await safeModalOperation(mockModalElement, operation);
            
            expect(result).toBe('result');
            expect(operation).toHaveBeenCalled();
            expect(mockModalElement.addEventListener).toHaveBeenCalled();
            expect(mockModalElement.removeEventListener).toHaveBeenCalled();
        });
    });
    
    describe('safeStateOperation', () => {
        it('should perform operation when not locked', async () => {
            const operation = vi.fn().mockResolvedValue('result');
            
            const result = await safeStateOperation(operation);
            
            expect(result).toBe('result');
            expect(operation).toHaveBeenCalled();
        });
        
        it('should retry when locked and retryOnLock is true', async () => {
            const operation = vi.fn().mockResolvedValue('result');
            
            // Lock initially
            (window as any).__structuredOutputInProgress = true;
            
            // Unlock after a delay
            setTimeout(() => {
                (window as any).__structuredOutputInProgress = false;
            }, 50);
            
            const result = await safeStateOperation(operation, { retryOnLock: true });
            
            expect(result).toBe('result');
            expect(operation).toHaveBeenCalled();
        });
        
        it('should throw error when locked and retryOnLock is false', async () => {
            (window as any).__structuredOutputInProgress = true;
            
            const operation = vi.fn().mockResolvedValue('result');
            
            await expect(safeStateOperation(operation, { retryOnLock: false }))
                .rejects.toThrow('Cannot perform operation while structured output is in progress');
        });
    });
    
    describe('initializeEventProtection', () => {
        it('should initialize event protection system', () => {
            const mockWindow = {
                addEventListener: vi.fn()
            } as any;
            
            // Mock global window
            const originalWindow = global.window;
            global.window = mockWindow;
            
            initializeEventProtection(true);
            
            expect(mockWindow.addEventListener).toHaveBeenCalledWith('error', expect.any(Function));
            expect(mockWindow.addEventListener).toHaveBeenCalledWith('beforeunload', expect.any(Function));
            expect((window as any).__structuredOutputDebug).toBe(true);
            
            // Restore original window
            global.window = originalWindow;
        });
    });
});