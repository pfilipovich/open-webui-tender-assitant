// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

// These tests run through the knowledge base functionality
describe('Knowledge Base', () => {
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

	context('Knowledge Base Management', () => {
		it('user can navigate to knowledge base', () => {
			cy.get('button').contains('Knowledge').click();
			cy.url().should('include', '/workspace/knowledge');
			cy.get('h1').should('contain', 'Knowledge');
		});

		it('user can create a new knowledge base', () => {
			cy.get('button').contains('Knowledge').click();
			cy.get('button[aria-label="Create Knowledge Base"]').click();
			
			// Fill in the form
			cy.get('input[placeholder="Knowledge Base Name"]').type('Test Knowledge Base');
			cy.get('textarea[placeholder="Description"]').type('A test knowledge base for Cypress');
			
			// Submit the form
			cy.get('button[type="submit"]').click();
			
			// Verify creation
			cy.get('.toast').should('contain', 'Knowledge base created successfully');
			cy.get('[data-testid="knowledge-item"]').should('contain', 'Test Knowledge Base');
		});

		it('user can view knowledge base details', () => {
			cy.get('button').contains('Knowledge').click();
			
			// Assuming we have a knowledge base to click on
			cy.get('[data-testid="knowledge-item"]').first().click();
			
			// Should navigate to knowledge base details
			cy.url().should('include', '/workspace/knowledge/');
			cy.get('h1').should('exist');
		});

		it('user can upload files to knowledge base', () => {
			cy.get('button').contains('Knowledge').click();
			cy.get('[data-testid="knowledge-item"]').first().click();
			
			// Click add content button
			cy.get('button[aria-label="Add Content"]').click();
			
			// Upload a file
			cy.get('input[type="file"]').selectFile('cypress/data/example-doc.txt');
			
			// Verify upload
			cy.get('.toast').should('contain', 'File uploaded successfully');
			cy.get('[data-testid="file-item"]').should('contain', 'example-doc.txt');
		});

		it('user can edit knowledge base', () => {
			cy.get('button').contains('Knowledge').click();
			cy.get('[data-testid="knowledge-item"]').first().click();
			
			// Click edit button
			cy.get('button[aria-label="Edit Knowledge Base"]').click();
			
			// Update description
			cy.get('textarea[placeholder="Description"]').clear().type('Updated description');
			
			// Save changes
			cy.get('button[type="submit"]').click();
			
			// Verify update
			cy.get('.toast').should('contain', 'Knowledge base updated successfully');
		});

		it('user can delete knowledge base', () => {
			cy.get('button').contains('Knowledge').click();
			cy.get('[data-testid="knowledge-item"]').first().click();
			
			// Click delete button
			cy.get('button[aria-label="Delete Knowledge Base"]').click();
			
			// Confirm deletion
			cy.get('button').contains('Delete').click();
			
			// Verify deletion
			cy.get('.toast').should('contain', 'Knowledge base deleted successfully');
			cy.url().should('include', '/workspace/knowledge');
		});

		it('user can search knowledge bases', () => {
			cy.get('button').contains('Knowledge').click();
			
			// Search for knowledge base
			cy.get('input[placeholder="Search knowledge bases"]').type('Test');
			
			// Verify search results
			cy.get('[data-testid="knowledge-item"]').should('have.length.greaterThan', 0);
		});

		it('user can filter knowledge bases', () => {
			cy.get('button').contains('Knowledge').click();
			
			// Apply filter
			cy.get('select[aria-label="Filter by"]').select('Recent');
			
			// Verify filtered results
			cy.get('[data-testid="knowledge-item"]').should('exist');
		});
	});

	context('Knowledge Base Files', () => {
		beforeEach(() => {
			cy.get('button').contains('Knowledge').click();
			cy.get('[data-testid="knowledge-item"]').first().click();
		});

		it('user can view file details', () => {
			cy.get('[data-testid="file-item"]').first().click();
			
			// Should show file details modal
			cy.get('[data-testid="file-details-modal"]').should('be.visible');
			cy.get('[data-testid="file-name"]').should('exist');
			cy.get('[data-testid="file-size"]').should('exist');
		});

		it('user can delete file from knowledge base', () => {
			cy.get('[data-testid="file-item"]').first().find('button[aria-label="Delete"]').click();
			
			// Confirm deletion
			cy.get('button').contains('Delete').click();
			
			// Verify file is removed
			cy.get('.toast').should('contain', 'File deleted successfully');
		});

		it('user can add text content directly', () => {
			cy.get('button[aria-label="Add Content"]').click();
			cy.get('button').contains('Add Text').click();
			
			// Fill in text content
			cy.get('input[placeholder="Content Title"]').type('Test Content');
			cy.get('textarea[placeholder="Content"]').type('This is test content for the knowledge base.');
			
			// Save content
			cy.get('button[type="submit"]').click();
			
			// Verify content added
			cy.get('.toast').should('contain', 'Content added successfully');
			cy.get('[data-testid="content-item"]').should('contain', 'Test Content');
		});

		it('user can bulk upload files', () => {
			cy.get('button[aria-label="Add Content"]').click();
			
			// Upload multiple files
			cy.get('input[type="file"]').selectFile([
				'cypress/data/example-doc.txt',
				'cypress/data/example-doc.txt'
			]);
			
			// Verify uploads
			cy.get('.toast').should('contain', 'Files uploaded successfully');
			cy.get('[data-testid="file-item"]').should('have.length.greaterThan', 1);
		});
	});

	context('Knowledge Base Integration', () => {
		it('user can use knowledge base in chat', () => {
			// Create a knowledge base first
			cy.get('button').contains('Knowledge').click();
			cy.get('button[aria-label="Create Knowledge Base"]').click();
			cy.get('input[placeholder="Knowledge Base Name"]').type('Chat Test KB');
			cy.get('button[type="submit"]').click();
			
			// Navigate to chat
			cy.visit('/');
			
			// Select model
			cy.get('button[aria-label="Select a model"]').click();
			cy.get('button[aria-label="model-item"]').first().click();
			
			// Use knowledge base in chat
			cy.get('#chat-input').type('&Chat Test KB What is this knowledge base about?');
			cy.get('button[type="submit"]').click();
			
			// Verify knowledge base is used
			cy.get('.chat-user').should('contain', 'Chat Test KB');
			cy.get('.chat-assistant', { timeout: 10_000 }).should('exist');
		});

		it('user can see knowledge base suggestions', () => {
			cy.visit('/');
			
			// Type ampersand to trigger knowledge base suggestions
			cy.get('#chat-input').type('&');
			
			// Should show knowledge base suggestions
			cy.get('[data-testid="knowledge-suggestions"]').should('be.visible');
			cy.get('[data-testid="knowledge-suggestion"]').should('have.length.greaterThan', 0);
		});
	});

	context('Knowledge Base Access Control', () => {
		it('admin can set knowledge base permissions', () => {
			cy.get('button').contains('Knowledge').click();
			cy.get('[data-testid="knowledge-item"]').first().click();
			
			// Open access control
			cy.get('button[aria-label="Access Control"]').click();
			
			// Set permissions
			cy.get('select[aria-label="Read Access"]').select('All Users');
			cy.get('select[aria-label="Write Access"]').select('Admin Only');
			
			// Save permissions
			cy.get('button').contains('Save').click();
			
			// Verify permissions saved
			cy.get('.toast').should('contain', 'Permissions updated successfully');
		});

		it('user can share knowledge base', () => {
			cy.get('button').contains('Knowledge').click();
			cy.get('[data-testid="knowledge-item"]').first().click();
			
			// Click share button
			cy.get('button[aria-label="Share Knowledge Base"]').click();
			
			// Copy share link
			cy.get('button').contains('Copy Link').click();
			
			// Verify link copied
			cy.get('.toast').should('contain', 'Link copied to clipboard');
		});
	});
});