// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

// These tests run through the tools functionality
describe('Tools Management', () => {
	// Wait for 2 seconds after all tests to fix an issue with Cypress's video recording missing the last few frames
	after(() => {
		// eslint-disable-next-line cypress/no-unnecessary-waiting
		cy.wait(2000);
	});

	beforeEach(() => {
		// Login as the admin user
		cy.loginAdmin();
		// Visit the workspace
		cy.visit('/workspace');
	});

	context('Tool Creation and Management', () => {
		it('user can navigate to tools page', () => {
			cy.get('button').contains('Tools').click();
			cy.url().should('include', '/workspace/tools');
			cy.get('h1').should('contain', 'Tools');
		});

		it('user can create a new tool', () => {
			cy.get('button').contains('Tools').click();
			cy.get('button[aria-label="Create Tool"]').click();
			
			// Fill in the form
			cy.get('input[placeholder="Tool Name"]').type('Test Calculator');
			cy.get('textarea[placeholder="Description"]').type('A test calculator tool');
			
			// Add tool code
			cy.get('textarea[placeholder="Tool Code"]').type(`
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Error: Invalid expression"
			`);
			
			// Submit the form
			cy.get('button[type="submit"]').click();
			
			// Verify creation
			cy.get('.toast').should('contain', 'Tool created successfully');
			cy.get('[data-testid="tool-item"]').should('contain', 'Test Calculator');
		});

		it('user can edit tool code', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Click edit button
			cy.get('button[aria-label="Edit Tool"]').click();
			
			// Update tool code
			cy.get('textarea[placeholder="Tool Code"]').clear().type(`
def calculate(expression: str) -> str:
    """Calculate a mathematical expression with enhanced error handling."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
			`);
			
			// Save changes
			cy.get('button[type="submit"]').click();
			
			// Verify update
			cy.get('.toast').should('contain', 'Tool updated successfully');
		});

		it('user can test tool functionality', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Click test button
			cy.get('button[aria-label="Test Tool"]').click();
			
			// Enter test input
			cy.get('input[placeholder="Test Input"]').type('2 + 2');
			
			// Execute test
			cy.get('button').contains('Execute').click();
			
			// Verify test result
			cy.get('[data-testid="test-output"]').should('contain', '4');
		});

		it('user can configure tool parameters', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Open parameters tab
			cy.get('button').contains('Parameters').click();
			
			// Add parameter
			cy.get('button[aria-label="Add Parameter"]').click();
			cy.get('input[placeholder="Parameter Name"]').type('precision');
			cy.get('select[aria-label="Parameter Type"]').select('number');
			cy.get('input[placeholder="Default Value"]').type('2');
			
			// Save parameters
			cy.get('button').contains('Save').click();
			
			// Verify parameters saved
			cy.get('.toast').should('contain', 'Parameters updated successfully');
		});

		it('user can delete tool', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Click delete button
			cy.get('button[aria-label="Delete Tool"]').click();
			
			// Confirm deletion
			cy.get('button').contains('Delete').click();
			
			// Verify deletion
			cy.get('.toast').should('contain', 'Tool deleted successfully');
			cy.url().should('include', '/workspace/tools');
		});
	});

	context('Tool Import and Export', () => {
		it('user can import tool from URL', () => {
			cy.get('button').contains('Tools').click();
			
			// Click import button
			cy.get('button[aria-label="Import Tool"]').click();
			
			// Enter URL
			cy.get('input[placeholder="Tool URL"]').type('https://raw.githubusercontent.com/example/tool.py');
			
			// Import tool
			cy.get('button').contains('Import').click();
			
			// Verify import
			cy.get('.toast').should('contain', 'Tool imported successfully');
		});

		it('user can export tool', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Click export button
			cy.get('button[aria-label="Export Tool"]').click();
			
			// Should download file
			cy.get('.toast').should('contain', 'Tool exported successfully');
		});

		it('user can import tool from file', () => {
			cy.get('button').contains('Tools').click();
			
			// Click import button
			cy.get('button[aria-label="Import Tool"]').click();
			
			// Upload tool file
			cy.get('input[type="file"]').selectFile('cypress/fixtures/tool.py');
			
			// Import tool
			cy.get('button').contains('Import').click();
			
			// Verify import
			cy.get('.toast').should('contain', 'Tool imported successfully');
		});
	});

	context('Tool Usage in Chat', () => {
		it('user can use tool in chat conversation', () => {
			// Navigate to chat
			cy.visit('/');
			
			// Select model
			cy.get('button[aria-label="Select a model"]').click();
			cy.get('button[aria-label="model-item"]').first().click();
			
			// Send message that should trigger tool usage
			cy.get('#chat-input').type('Calculate 15 * 23');
			cy.get('button[type="submit"]').click();
			
			// Verify tool was used
			cy.get('.chat-user').should('contain', 'Calculate 15 * 23');
			cy.get('.chat-assistant', { timeout: 10_000 }).should('exist');
			cy.get('[data-testid="tool-call"]').should('be.visible');
		});

		it('user can see tool execution results', () => {
			cy.visit('/');
			
			// Select model
			cy.get('button[aria-label="Select a model"]').click();
			cy.get('button[aria-label="model-item"]').first().click();
			
			// Send message with tool usage
			cy.get('#chat-input').type('What is 100 divided by 4?');
			cy.get('button[type="submit"]').click();
			
			// Verify tool execution
			cy.get('.chat-assistant', { timeout: 10_000 }).should('exist');
			cy.get('[data-testid="tool-result"]').should('contain', '25');
		});
	});

	context('Tool Access Control', () => {
		it('admin can set tool permissions', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Open access control
			cy.get('button[aria-label="Access Control"]').click();
			
			// Set permissions
			cy.get('select[aria-label="Access Level"]').select('All Users');
			cy.get('input[name="allow_modification"]').check();
			
			// Save permissions
			cy.get('button').contains('Save').click();
			
			// Verify permissions saved
			cy.get('.toast').should('contain', 'Permissions updated successfully');
		});

		it('user can share tool', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Click share button
			cy.get('button[aria-label="Share Tool"]').click();
			
			// Copy share link
			cy.get('button').contains('Copy Link').click();
			
			// Verify link copied
			cy.get('.toast').should('contain', 'Link copied to clipboard');
		});
	});

	context('Tool Categories and Organization', () => {
		it('user can categorize tools', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Open settings
			cy.get('button[aria-label="Tool Settings"]').click();
			
			// Set category
			cy.get('select[aria-label="Category"]').select('Math');
			cy.get('input[name="tags"]').type('calculator, math, utility');
			
			// Save settings
			cy.get('button').contains('Save').click();
			
			// Verify categorization
			cy.get('.toast').should('contain', 'Tool settings updated');
		});

		it('user can filter tools by category', () => {
			cy.get('button').contains('Tools').click();
			
			// Apply category filter
			cy.get('select[aria-label="Filter by Category"]').select('Math');
			
			// Verify filtered results
			cy.get('[data-testid="tool-item"]').should('have.length.greaterThan', 0);
		});

		it('user can search tools', () => {
			cy.get('button').contains('Tools').click();
			
			// Search for tools
			cy.get('input[placeholder="Search tools"]').type('calculator');
			
			// Verify search results
			cy.get('[data-testid="tool-item"]').should('contain', 'calculator');
		});
	});

	context('Tool Validation and Security', () => {
		it('user can validate tool code', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Click validate button
			cy.get('button[aria-label="Validate Tool"]').click();
			
			// Should show validation results
			cy.get('[data-testid="validation-results"]').should('be.visible');
			cy.get('[data-testid="validation-status"]').should('contain', 'Valid');
		});

		it('user can see tool security warnings', () => {
			cy.get('button').contains('Tools').click();
			
			// Create tool with potentially unsafe code
			cy.get('button[aria-label="Create Tool"]').click();
			cy.get('input[placeholder="Tool Name"]').type('Unsafe Tool');
			cy.get('textarea[placeholder="Tool Code"]').type(`
import os
def dangerous_function():
    os.system('rm -rf /')
			`);
			
			// Submit and expect warning
			cy.get('button[type="submit"]').click();
			
			// Should show security warning
			cy.get('[data-testid="security-warning"]').should('be.visible');
			cy.get('[data-testid="security-warning"]').should('contain', 'potentially dangerous');
		});
	});

	context('Tool Performance and Monitoring', () => {
		it('user can view tool usage statistics', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Open statistics tab
			cy.get('button').contains('Statistics').click();
			
			// Should show usage charts
			cy.get('[data-testid="usage-chart"]').should('be.visible');
			cy.get('[data-testid="execution-count"]').should('exist');
			cy.get('[data-testid="success-rate"]').should('exist');
		});

		it('user can view tool execution logs', () => {
			cy.get('button').contains('Tools').click();
			cy.get('[data-testid="tool-item"]').first().click();
			
			// Open logs tab
			cy.get('button').contains('Logs').click();
			
			// Should show execution logs
			cy.get('[data-testid="execution-log"]').should('be.visible');
			cy.get('[data-testid="log-entry"]').should('have.length.greaterThan', 0);
		});
	});
});