import { describe, it, expect, vi } from 'vitest';
import {
	sleep,
	replaceTokens,
	sanitizeResponseContent,
	processResponseContent,
	capitalizeFirstLetter,
	splitStream,
	convertMessagesToHistory,
	getGravatarURL,
	formatDate,
	copyToClipboard,
	compareVersion,
	extractCurlyBraceWords,
	removeLastWordFromString,
	removeFirstHashWord,
	transformFileName,
	calculateSHA256,
	isValidHttpUrl,
	removeEmojis,
	removeFormattings,
	cleanText,
	extractSentences,
	extractFrontmatter,
	getFormattedDate,
	getFormattedTime,
	getCurrentDateTime,
	getUserTimezone,
	getWeekday,
	formatFileSize,
	getLineCount,
	slugify
} from './index';

describe('Utility Functions', () => {
	describe('sleep', () => {
		it('should resolve after specified milliseconds', async () => {
			const start = Date.now();
			await sleep(50);
			const end = Date.now();
			expect(end - start).toBeGreaterThanOrEqual(40);
		});
	});

	describe('replaceTokens', () => {
		it('should replace {{char}} and {{user}} tokens', () => {
			const content = 'Hello {{user}}, I am {{char}}';
			const result = replaceTokens(content, [], 'Assistant', 'John');
			expect(result).toBe('Hello John, I am Assistant');
		});

		it('should replace video file tokens', () => {
			const content = 'Video: {{VIDEO_FILE_ID_123e4567-e89b-12d3-a456-426614174000}}';
			const result = replaceTokens(content, [], 'Assistant', 'John');
			expect(result).toContain('<video src="');
			expect(result).toContain('123e4567-e89b-12d3-a456-426614174000');
		});

		it('should replace HTML file tokens', () => {
			const content = 'HTML: {{HTML_FILE_ID_123e4567-e89b-12d3-a456-426614174000}}';
			const result = replaceTokens(content, [], 'Assistant', 'John');
			expect(result).toContain('<file type="html" id="123e4567-e89b-12d3-a456-426614174000"');
		});

		it('should replace source IDs', () => {
			const content = 'Reference [1] and [2]';
			const sourceIds = ['doc1.pdf', 'doc2.pdf'];
			const result = replaceTokens(content, sourceIds, 'Assistant', 'John');
			expect(result).toContain('<source_id data="1" title="doc1.pdf"');
			expect(result).toContain('<source_id data="2" title="doc2.pdf"');
		});
	});

	describe('sanitizeResponseContent', () => {
		it('should remove incomplete tokens at the end', () => {
			const content = 'Hello world<|im_start|>';
			const result = sanitizeResponseContent(content);
			expect(result).toBe('Hello world');
		});

		it('should remove incomplete tokens without closing', () => {
			const content = 'Hello world<|im';
			const result = sanitizeResponseContent(content);
			expect(result).toBe('Hello world');
		});

		it('should remove complete tokens', () => {
			const content = 'Hello <|im_start|> world <|im_end|>';
			const result = sanitizeResponseContent(content);
			expect(result).toBe('Hello   world');
		});

		it('should escape HTML characters', () => {
			const content = 'Hello <script>alert("xss")</script>';
			const result = sanitizeResponseContent(content);
			expect(result).toBe('Hello &lt;script&gt;alert("xss")&lt;/script&gt;');
		});
	});

	describe('processResponseContent', () => {
		it('should process and trim content', () => {
			const content = '  Hello world  ';
			const result = processResponseContent(content);
			expect(result).toBe('Hello world');
		});

		it('should handle Chinese content', () => {
			const content = '你好世界';
			const result = processResponseContent(content);
			expect(result).toBe('你好世界');
		});
	});

	describe('capitalizeFirstLetter', () => {
		it('should capitalize first letter', () => {
			expect(capitalizeFirstLetter('hello')).toBe('Hello');
			expect(capitalizeFirstLetter('world')).toBe('World');
		});

		it('should handle empty string', () => {
			expect(capitalizeFirstLetter('')).toBe('');
		});
	});

	describe('getGravatarURL', () => {
		it('should generate gravatar URL', () => {
			const email = 'test@example.com';
			const url = getGravatarURL(email);
			expect(url).toContain('https://www.gravatar.com/avatar/');
			expect(url).toMatch(/^https:\/\/www\.gravatar\.com\/avatar\/[a-f0-9]{64}$/);
		});

		it('should handle email case and whitespace', () => {
			const url1 = getGravatarURL('  TEST@EXAMPLE.COM  ');
			const url2 = getGravatarURL('test@example.com');
			expect(url1).toBe(url2);
		});
	});

	describe('compareVersion', () => {
		it('should compare versions correctly', () => {
			expect(compareVersion('1.0.1', '1.0.0')).toBe(true);
			expect(compareVersion('1.0.0', '1.0.1')).toBe(false);
			expect(compareVersion('1.0.0', '1.0.0')).toBe(false);
		});

		it('should handle different version formats', () => {
			expect(compareVersion('1.0', '1.0.0')).toBe(false);
			expect(compareVersion('1.0.0', '1.0')).toBe(true);
		});
	});

	describe('extractCurlyBraceWords', () => {
		it('should extract words in curly braces', () => {
			const text = 'Hello {user}, welcome to {app}!';
			const result = extractCurlyBraceWords(text);
			expect(result).toEqual(['user', 'app']);
		});

		it('should handle text without curly braces', () => {
			const text = 'Hello world';
			const result = extractCurlyBraceWords(text);
			expect(result).toEqual([]);
		});
	});

	describe('removeLastWordFromString', () => {
		it('should remove specific word from end', () => {
			const text = 'Hello world test';
			const result = removeLastWordFromString(text, 'test');
			expect(result).toBe('Hello world');
		});

		it('should not remove if word not at end', () => {
			const text = 'Hello test world';
			const result = removeLastWordFromString(text, 'test');
			expect(result).toBe('Hello test world');
		});
	});

	describe('removeFirstHashWord', () => {
		it('should remove first hash word', () => {
			const text = '#tag Hello world #another';
			const result = removeFirstHashWord(text);
			expect(result).toBe('Hello world #another');
		});

		it('should handle text without hash', () => {
			const text = 'Hello world';
			const result = removeFirstHashWord(text);
			expect(result).toBe('Hello world');
		});
	});

	describe('transformFileName', () => {
		it('should transform filename', () => {
			const fileName = 'My Document.pdf';
			const result = transformFileName(fileName);
			expect(result).toBe('My-Document.pdf');
		});

		it('should handle special characters', () => {
			const fileName = 'Test@File#Name$.txt';
			const result = transformFileName(fileName);
			expect(result).toBe('Test-File-Name-.txt');
		});
	});

	describe('isValidHttpUrl', () => {
		it('should validate HTTP URLs', () => {
			expect(isValidHttpUrl('https://example.com')).toBe(true);
			expect(isValidHttpUrl('http://example.com')).toBe(true);
			expect(isValidHttpUrl('https://example.com/path?query=value')).toBe(true);
		});

		it('should reject invalid URLs', () => {
			expect(isValidHttpUrl('not-a-url')).toBe(false);
			expect(isValidHttpUrl('ftp://example.com')).toBe(false);
			expect(isValidHttpUrl('')).toBe(false);
		});
	});

	describe('removeEmojis', () => {
		it('should remove emoji characters', () => {
			const text = 'Hello 😊 World 🌍';
			const result = removeEmojis(text);
			expect(result).toBe('Hello  World ');
		});

		it('should handle text without emojis', () => {
			const text = 'Hello World';
			const result = removeEmojis(text);
			expect(result).toBe('Hello World');
		});
	});

	describe('removeFormattings', () => {
		it('should remove markdown formatting', () => {
			const text = '**bold** and *italic* text';
			const result = removeFormattings(text);
			expect(result).toBe('bold and italic text');
		});

		it('should handle text without formatting', () => {
			const text = 'plain text';
			const result = removeFormattings(text);
			expect(result).toBe('plain text');
		});
	});

	describe('cleanText', () => {
		it('should clean text content', () => {
			const content = '  Hello\n\nWorld  ';
			const result = cleanText(content);
			expect(result).toBe('Hello World');
		});

		it('should handle empty content', () => {
			const content = '';
			const result = cleanText(content);
			expect(result).toBe('');
		});
	});

	describe('extractSentences', () => {
		it('should extract sentences from text', () => {
			const text = 'First sentence. Second sentence! Third sentence?';
			const result = extractSentences(text);
			expect(result).toEqual(['First sentence.', 'Second sentence!', 'Third sentence?']);
		});

		it('should handle single sentence', () => {
			const text = 'Single sentence.';
			const result = extractSentences(text);
			expect(result).toEqual(['Single sentence.']);
		});
	});

	describe('extractFrontmatter', () => {
		it('should extract frontmatter from content', () => {
			const content = '---\ntitle: Test\nauthor: John\n---\n\nContent here';
			const result = extractFrontmatter(content);
			expect(result.frontmatter).toEqual({ title: 'Test', author: 'John' });
			expect(result.content).toBe('Content here');
		});

		it('should handle content without frontmatter', () => {
			const content = 'Just regular content';
			const result = extractFrontmatter(content);
			expect(result.frontmatter).toEqual({});
			expect(result.content).toBe('Just regular content');
		});
	});

	describe('formatFileSize', () => {
		it('should format file sizes correctly', () => {
			expect(formatFileSize(0)).toBe('0 B');
			expect(formatFileSize(1024)).toBe('1.0 KB');
			expect(formatFileSize(1024 * 1024)).toBe('1.0 MB');
			expect(formatFileSize(1024 * 1024 * 1024)).toBe('1.0 GB');
		});

		it('should handle decimal places', () => {
			expect(formatFileSize(1536)).toBe('1.5 KB');
			expect(formatFileSize(1536 * 1024)).toBe('1.5 MB');
		});
	});

	describe('getLineCount', () => {
		it('should count lines in text', () => {
			const text = 'Line 1\nLine 2\nLine 3';
			const result = getLineCount(text);
			expect(result).toBe(3);
		});

		it('should handle empty text', () => {
			const text = '';
			const result = getLineCount(text);
			expect(result).toBe(0);
		});

		it('should handle single line', () => {
			const text = 'Single line';
			const result = getLineCount(text);
			expect(result).toBe(1);
		});
	});

	describe('slugify', () => {
		it('should create URL-friendly slugs', () => {
			expect(slugify('Hello World')).toBe('hello-world');
			expect(slugify('Test String!')).toBe('test-string');
			expect(slugify('Multiple   Spaces')).toBe('multiple-spaces');
		});

		it('should handle special characters', () => {
			expect(slugify('Test@#$%^&*()String')).toBe('test-string');
			expect(slugify('café')).toBe('cafe');
		});

		it('should handle empty string', () => {
			expect(slugify('')).toBe('');
		});
	});

	describe('getFormattedDate', () => {
		it('should return formatted date', () => {
			const result = getFormattedDate();
			expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
		});
	});

	describe('getFormattedTime', () => {
		it('should return formatted time', () => {
			const result = getFormattedTime();
			expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
		});
	});

	describe('getCurrentDateTime', () => {
		it('should return current datetime', () => {
			const result = getCurrentDateTime();
			expect(result).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
		});
	});

	describe('getUserTimezone', () => {
		it('should return user timezone', () => {
			const result = getUserTimezone();
			expect(typeof result).toBe('string');
			expect(result.length).toBeGreaterThan(0);
		});
	});

	describe('getWeekday', () => {
		it('should return current weekday', () => {
			const result = getWeekday();
			expect(typeof result).toBe('string');
			expect(result.length).toBeGreaterThan(0);
		});
	});
});