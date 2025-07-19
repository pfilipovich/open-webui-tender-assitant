// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

// These tests run through the model management functionality
describe('Model Management', () => {
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

	context('Model Configuration', () => {
		it('user can navigate to models page', () => {
			cy.get('button').contains('Models').click();
			cy.url().should('include', '/workspace/models');
			cy.get('h1').should('contain', 'Models');
		});

		it('user can create a new model', () => {
			cy.get('button').contains('Models').click();
			cy.get('button[aria-label="Create Model"]').click();
			
			// Fill in the form
			cy.get('input[placeholder="Model Name"]').type('Test Model');
			cy.get('input[placeholder="Base Model"]').type('llama3');
			cy.get('textarea[placeholder="Description"]').type('A test model for Cypress');
			
			// Submit the form
			cy.get('button[type="submit"]').click();
			
			// Verify creation
			cy.get('.toast').should('contain', 'Model created successfully');
			cy.get('[data-testid="model-item"]').should('contain', 'Test Model');
		});

		it('user can edit model configuration', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Click edit button
			cy.get('button[aria-label="Edit Model"]').click();
			
			// Update description
			cy.get('textarea[placeholder="Description"]').clear().type('Updated model description');
			
			// Save changes
			cy.get('button[type="submit"]').click();
			
			// Verify update
			cy.get('.toast').should('contain', 'Model updated successfully');
		});

		it('user can configure model parameters', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Open parameters tab
			cy.get('button').contains('Parameters').click();
			
			// Adjust temperature
			cy.get('input[name="temperature"]').clear().type('0.8');
			
			// Adjust max tokens
			cy.get('input[name="max_tokens"]').clear().type('2048');
			
			// Save parameters
			cy.get('button').contains('Save').click();
			
			// Verify parameters saved
			cy.get('.toast').should('contain', 'Parameters updated successfully');
		});

		it('user can set model capabilities', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Open capabilities tab
			cy.get('button').contains('Capabilities').click();
			
			// Enable vision capability
			cy.get('input[name="vision"]').check();
			
			// Enable function calling
			cy.get('input[name="function_calling"]').check();
			
			// Save capabilities
			cy.get('button').contains('Save').click();
			
			// Verify capabilities saved
			cy.get('.toast').should('contain', 'Capabilities updated successfully');
		});

		it('user can delete model', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Click delete button
			cy.get('button[aria-label="Delete Model"]').click();
			
			// Confirm deletion
			cy.get('button').contains('Delete').click();
			
			// Verify deletion
			cy.get('.toast').should('contain', 'Model deleted successfully');
			cy.url().should('include', '/workspace/models');
		});
	});

	context('Model Tools Integration', () => {
		beforeEach(() => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
		});

		it('user can assign tools to model', () => {
			// Open tools tab
			cy.get('button').contains('Tools').click();
			
			// Select available tools
			cy.get('input[name="calculator"]').check();
			cy.get('input[name="web_search"]').check();
			
			// Save tool assignments
			cy.get('button').contains('Save').click();
			
			// Verify tools assigned
			cy.get('.toast').should('contain', 'Tools updated successfully');
		});

		it('user can configure tool parameters', () => {
			cy.get('button').contains('Tools').click();
			
			// Click tool configuration
			cy.get('button[aria-label="Configure Tool"]').first().click();
			
			// Update tool parameters
			cy.get('input[name="api_key"]').type('test-api-key');
			cy.get('input[name="max_results"]').clear().type('10');
			
			// Save configuration
			cy.get('button').contains('Save').click();
			
			// Verify configuration saved
			cy.get('.toast').should('contain', 'Tool configuration updated');
		});
	});

	context('Model Knowledge Integration', () => {
		beforeEach(() => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
		});

		it('user can assign knowledge bases to model', () => {
			// Open knowledge tab
			cy.get('button').contains('Knowledge').click();
			
			// Select available knowledge bases
			cy.get('input[name="documentation"]').check();
			cy.get('input[name="faq"]').check();
			
			// Save knowledge assignments
			cy.get('button').contains('Save').click();
			
			// Verify knowledge assigned
			cy.get('.toast').should('contain', 'Knowledge bases updated successfully');
		});

		it('user can configure knowledge retrieval settings', () => {
			cy.get('button').contains('Knowledge').click();
			
			// Configure retrieval settings
			cy.get('input[name="max_documents"]').clear().type('5');
			cy.get('input[name="relevance_threshold"]').clear().type('0.7');
			
			// Save settings
			cy.get('button').contains('Save').click();
			
			// Verify settings saved
			cy.get('.toast').should('contain', 'Retrieval settings updated');
		});
	});

	context('Model Testing', () => {
		it('user can test model in playground', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Click test button
			cy.get('button[aria-label="Test Model"]').click();
			
			// Should navigate to playground
			cy.url().should('include', '/playground');
			
			// Test the model
			cy.get('textarea[placeholder="Enter your message"]').type('Hello, test message');
			cy.get('button[type="submit"]').click();
			
			// Verify response
			cy.get('.message-user').should('contain', 'Hello, test message');
			cy.get('.message-assistant', { timeout: 10_000 }).should('exist');
		});

		it('user can validate model configuration', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Click validate button
			cy.get('button[aria-label="Validate Model"]').click();
			
			// Should show validation results
			cy.get('[data-testid="validation-results"]').should('be.visible');
			cy.get('[data-testid="validation-status"]').should('contain', 'Valid');
		});
	});

	context('Model Import/Export', () => {
		it('user can export model configuration', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Click export button
			cy.get('button[aria-label="Export Model"]').click();
			
			// Should download file
			cy.get('.toast').should('contain', 'Model exported successfully');
		});

		it('user can import model configuration', () => {
			cy.get('button').contains('Models').click();
			
			// Click import button
			cy.get('button[aria-label="Import Model"]').click();
			
			// Upload model file
			cy.get('input[type="file"]').selectFile('cypress/fixtures/model-config.json');
			
			// Submit import
			cy.get('button').contains('Import').click();
			
			// Verify import
			cy.get('.toast').should('contain', 'Model imported successfully');
		});
	});

	context('Model Access Control', () => {
		it('admin can set model permissions', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Open access control
			cy.get('button[aria-label="Access Control"]').click();
			
			// Set permissions
			cy.get('select[aria-label="Access Level"]').select('Admin Only');
			
			// Save permissions
			cy.get('button').contains('Save').click();
			
			// Verify permissions saved
			cy.get('.toast').should('contain', 'Permissions updated successfully');
		});

		it('user can share model', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Click share button
			cy.get('button[aria-label="Share Model"]').click();
			
			// Copy share link
			cy.get('button').contains('Copy Link').click();
			
			// Verify link copied
			cy.get('.toast').should('contain', 'Link copied to clipboard');
		});
	});

	context('Model Monitoring', () => {
		it('user can view model usage statistics', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Open statistics tab
			cy.get('button').contains('Statistics').click();
			
			// Should show usage charts
			cy.get('[data-testid="usage-chart"]').should('be.visible');
			cy.get('[data-testid="token-usage"]').should('exist');
			cy.get('[data-testid="request-count"]').should('exist');
		});

		it('user can view model performance metrics', () => {
			cy.get('button').contains('Models').click();
			cy.get('[data-testid="model-item"]').first().click();
			
			// Open performance tab
			cy.get('button').contains('Performance').click();
			
			// Should show performance metrics
			cy.get('[data-testid="response-time"]').should('exist');
			cy.get('[data-testid="success-rate"]').should('exist');
			cy.get('[data-testid="error-rate"]').should('exist');
		});
	});
});