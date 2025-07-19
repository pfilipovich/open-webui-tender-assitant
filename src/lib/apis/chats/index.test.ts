import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
	createNewChat,
	importChat,
	getChatList,
	getChatById,
	updateChatById,
	deleteChatById,
	cloneChatById,
	archiveChatById,
	shareChatById,
	deleteSharedChatById,
	getAllChats,
	getArchivedChats,
	archiveAllChats,
	deleteAllChats,
	getChatsByFolderId,
	getChatListByTagName,
	getChatListByUserId,
	getChatUserProfile,
	updateChatUserProfile,
	deleteChatUserProfile,
	exportChats,
	importChats
} from './index';

// Mock the constants
vi.mock('$lib/constants', () => ({
	WEBUI_API_BASE_URL: 'http://localhost:8080/api/v1'
}));

// Mock the utils
vi.mock('$lib/utils', () => ({
	getTimeRange: vi.fn(() => ({ start: '2023-01-01', end: '2023-12-31' }))
}));

describe('Chat API Functions', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		global.fetch = vi.fn();
	});

	describe('createNewChat', () => {
		it('should create a new chat successfully', async () => {
			const mockResponse = {
				id: 'chat-123',
				title: 'New Chat',
				created_at: '2023-01-01T00:00:00Z'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chat = { title: 'New Chat' };
			const result = await createNewChat(token, chat);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/new',
				{
					method: 'POST',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					},
					body: JSON.stringify({ chat })
				}
			);

			expect(result).toEqual(mockResponse);
		});

		it('should handle API error', async () => {
			const mockError = { error: 'Invalid request' };

			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				json: () => Promise.resolve(mockError)
			});

			const token = 'test-token';
			const chat = { title: 'New Chat' };

			await expect(createNewChat(token, chat)).rejects.toEqual(mockError);
		});

		it('should handle network error', async () => {
			global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

			const token = 'test-token';
			const chat = { title: 'New Chat' };

			await expect(createNewChat(token, chat)).rejects.toThrow('Network error');
		});
	});

	describe('importChat', () => {
		it('should import a chat successfully', async () => {
			const mockResponse = {
				id: 'chat-123',
				title: 'Imported Chat',
				created_at: '2023-01-01T00:00:00Z'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chat = { title: 'Imported Chat' };
			const meta = { source: 'export' };
			const pinned = true;
			const folderId = 'folder-123';

			const result = await importChat(token, chat, meta, pinned, folderId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/import',
				{
					method: 'POST',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					},
					body: JSON.stringify({
						chat,
						meta,
						pinned,
						folder_id: folderId
					})
				}
			);

			expect(result).toEqual(mockResponse);
		});

		it('should handle optional parameters', async () => {
			const mockResponse = {
				id: 'chat-123',
				title: 'Imported Chat'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chat = { title: 'Imported Chat' };
			const meta = null;

			const result = await importChat(token, chat, meta);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/import',
				{
					method: 'POST',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					},
					body: JSON.stringify({
						chat,
						meta,
						pinned: undefined,
						folder_id: undefined
					})
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('getChatList', () => {
		it('should get chat list successfully', async () => {
			const mockResponse = [
				{ id: 'chat-1', title: 'Chat 1' },
				{ id: 'chat-2', title: 'Chat 2' }
			];

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const result = await getChatList(token);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/',
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});

		it('should handle empty chat list', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve([])
			});

			const token = 'test-token';
			const result = await getChatList(token);

			expect(result).toEqual([]);
		});
	});

	describe('getChatById', () => {
		it('should get chat by ID successfully', async () => {
			const mockResponse = {
				id: 'chat-123',
				title: 'Test Chat',
				messages: []
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chatId = 'chat-123';
			const result = await getChatById(token, chatId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123',
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});

		it('should handle chat not found', async () => {
			const mockError = { error: 'Chat not found' };

			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				json: () => Promise.resolve(mockError)
			});

			const token = 'test-token';
			const chatId = 'non-existent-chat';

			await expect(getChatById(token, chatId)).rejects.toEqual(mockError);
		});
	});

	describe('updateChatById', () => {
		it('should update chat successfully', async () => {
			const mockResponse = {
				id: 'chat-123',
				title: 'Updated Chat',
				updated_at: '2023-01-01T00:00:00Z'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chatId = 'chat-123';
			const chat = { title: 'Updated Chat' };

			const result = await updateChatById(token, chatId, chat);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123',
				{
					method: 'POST',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					},
					body: JSON.stringify({ chat })
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('deleteChatById', () => {
		it('should delete chat successfully', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(true)
			});

			const token = 'test-token';
			const chatId = 'chat-123';

			const result = await deleteChatById(token, chatId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123',
				{
					method: 'DELETE',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toBe(true);
		});

		it('should handle delete failure', async () => {
			const mockError = { error: 'Cannot delete chat' };

			global.fetch = vi.fn().mockResolvedValue({
				ok: false,
				json: () => Promise.resolve(mockError)
			});

			const token = 'test-token';
			const chatId = 'chat-123';

			await expect(deleteChatById(token, chatId)).rejects.toEqual(mockError);
		});
	});

	describe('cloneChatById', () => {
		it('should clone chat successfully', async () => {
			const mockResponse = {
				id: 'chat-456',
				title: 'Clone of Original Chat',
				created_at: '2023-01-01T00:00:00Z'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chatId = 'chat-123';

			const result = await cloneChatById(token, chatId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123/clone',
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('archiveChatById', () => {
		it('should archive chat successfully', async () => {
			const mockResponse = {
				id: 'chat-123',
				archived: true,
				archived_at: '2023-01-01T00:00:00Z'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chatId = 'chat-123';

			const result = await archiveChatById(token, chatId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123/archive',
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('shareChatById', () => {
		it('should share chat successfully', async () => {
			const mockResponse = {
				id: 'chat-123',
				share_id: 'share-456',
				shared_at: '2023-01-01T00:00:00Z'
			};

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const chatId = 'chat-123';

			const result = await shareChatById(token, chatId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123/share',
				{
					method: 'POST',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('deleteSharedChatById', () => {
		it('should delete shared chat successfully', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(true)
			});

			const token = 'test-token';
			const chatId = 'chat-123';

			const result = await deleteSharedChatById(token, chatId);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/chat-123/share',
				{
					method: 'DELETE',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toBe(true);
		});
	});

	describe('getAllChats', () => {
		it('should get all chats successfully', async () => {
			const mockResponse = [
				{ id: 'chat-1', title: 'Chat 1' },
				{ id: 'chat-2', title: 'Chat 2' }
			];

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const result = await getAllChats(token);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/all',
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('getArchivedChats', () => {
		it('should get archived chats successfully', async () => {
			const mockResponse = [
				{ id: 'chat-1', title: 'Archived Chat 1', archived: true },
				{ id: 'chat-2', title: 'Archived Chat 2', archived: true }
			];

			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const token = 'test-token';
			const result = await getArchivedChats(token);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/all/archived',
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toEqual(mockResponse);
		});
	});

	describe('archiveAllChats', () => {
		it('should archive all chats successfully', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(true)
			});

			const token = 'test-token';
			const result = await archiveAllChats(token);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/archive/all',
				{
					method: 'POST',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toBe(true);
		});
	});

	describe('deleteAllChats', () => {
		it('should delete all chats successfully', async () => {
			global.fetch = vi.fn().mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(true)
			});

			const token = 'test-token';
			const result = await deleteAllChats(token);

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8080/api/v1/chats/',
				{
					method: 'DELETE',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: 'Bearer test-token'
					}
				}
			);

			expect(result).toBe(true);
		});
	});
});