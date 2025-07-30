/**
 * Export utilities for checklist results
 */

interface ChecklistResult {
	prompt: string;
	promptTitle?: string;
	promptCommand?: string;
	response: string;
	rawResponse?: string; // Store original JSON
	structured_output?: boolean; // Flag for structured responses
	schema?: string; // Store schema used
	error: boolean;
	validation_error?: string; // Schema validation errors
}

/**
 * Convert checklist results to CSV format
 */
export const exportToCSV = (checklistResults: ChecklistResult[], filename?: string): void => {
	if (!checklistResults || checklistResults.length === 0) {
		throw new Error('No checklist data to export');
	}

	// Enhanced CSV headers for structured output support
	const headers = ['Prompt Name', 'Prompt', 'Response', 'Structured Output', 'Raw JSON', 'Schema Used', 'Status', 'Validation Error'];
	
	// Convert data to CSV rows
	const csvRows = [headers.join(',')];
	
	checklistResults.forEach(result => {
		const promptName = `"${(result.promptTitle || result.promptCommand || 'Untitled').replace(/"/g, '""')}"`;
		const prompt = `"${(result.prompt || '').replace(/"/g, '""')}"`;
		const response = `"${(result.response || '').replace(/"/g, '""')}"`;
		const structuredOutput = result.structured_output ? 'Yes' : 'No';
		const rawJson = result.rawResponse ? `"${result.rawResponse.replace(/"/g, '""')}"` : '';
		const schemaUsed = result.schema ? `"${result.schema.replace(/"/g, '""')}"` : '';
		const status = result.error ? 'Error' : 'Success';
		const validationError = result.validation_error ? `"${result.validation_error.replace(/"/g, '""')}"` : '';
		
		csvRows.push([
			promptName, 
			prompt, 
			response, 
			structuredOutput, 
			rawJson, 
			schemaUsed, 
			status, 
			validationError
		].join(','));
	});
	
	const csvContent = csvRows.join('\n');
	const timestamp = generateTimestampUID();
	const defaultFilename = filename || `checklist-results-${timestamp}.csv`;
	
	downloadFile(csvContent, defaultFilename, 'text/csv');
};

/**
 * Convert checklist results to Excel format using simple HTML table approach
 */
export const exportToExcel = (checklistResults: ChecklistResult[], filename?: string): void => {
	if (!checklistResults || checklistResults.length === 0) {
		throw new Error('No checklist data to export');
	}

	// Create HTML table for Excel with enhanced columns
	let htmlContent = `
		<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
		<head>
			<meta charset="utf-8">
			<meta name="ProgId" content="Excel.Sheet">
		</head>
		<body>
		<table border="1">
			<tr style="background-color: #4CAF50; color: white; font-weight: bold;">
				<th style="padding: 8px;">Prompt Name</th>
				<th style="padding: 8px;">Prompt</th>
				<th style="padding: 8px;">Response</th>
				<th style="padding: 8px;">Structured Output</th>
				<th style="padding: 8px;">Raw JSON</th>
				<th style="padding: 8px;">Schema Used</th>
				<th style="padding: 8px;">Status</th>
				<th style="padding: 8px;">Validation Error</th>
			</tr>
	`;

	checklistResults.forEach(result => {
		const promptNameHtml = escapeHtml(result.promptTitle || result.promptCommand || 'Untitled');
		const promptHtml = escapeHtml(result.prompt || '');
		const responseHtml = escapeHtml(result.response || '');
		const structuredOutputHtml = result.structured_output ? 'Yes' : 'No';
		const rawJsonHtml = escapeHtml(result.rawResponse || '');
		const schemaUsedHtml = escapeHtml(result.schema || '');
		const statusHtml = result.error ? 'Error' : 'Success';
		const validationErrorHtml = escapeHtml(result.validation_error || '');
		
		const rowStyle = result.error ? 'background-color: #ffebee;' : 
						result.structured_output ? 'background-color: #e8f5e8;' : '';
		
		htmlContent += `
			<tr style="${rowStyle}">
				<td style="padding: 8px; vertical-align: top; white-space: pre-wrap;">${promptNameHtml}</td>
				<td style="padding: 8px; vertical-align: top; white-space: pre-wrap;">${promptHtml}</td>
				<td style="padding: 8px; vertical-align: top; white-space: pre-wrap;">${responseHtml}</td>
				<td style="padding: 8px; vertical-align: top; text-align: center;">${structuredOutputHtml}</td>
				<td style="padding: 8px; vertical-align: top; white-space: pre-wrap; font-family: monospace; font-size: 11px;">${rawJsonHtml}</td>
				<td style="padding: 8px; vertical-align: top; white-space: pre-wrap; font-family: monospace; font-size: 11px;">${schemaUsedHtml}</td>
				<td style="padding: 8px; vertical-align: top; text-align: center; font-weight: bold;">${statusHtml}</td>
				<td style="padding: 8px; vertical-align: top; white-space: pre-wrap; color: red;">${validationErrorHtml}</td>
			</tr>
		`;
	});

	htmlContent += `
		</table>
		</body>
		</html>
	`;

	const timestamp = generateTimestampUID();
	const defaultFilename = filename || `checklist-results-${timestamp}.xls`;
	
	downloadFile(htmlContent, defaultFilename, 'application/vnd.ms-excel');
};

/**
 * Export checklist results with enhanced Excel using xlsx library
 */
export const exportToXLSX = async (checklistResults: ChecklistResult[], filename?: string): Promise<void> => {
	if (!checklistResults || checklistResults.length === 0) {
		throw new Error('No checklist data to export');
	}

	try {
		// Dynamic import to avoid bundling xlsx unless needed
		const XLSX = await import('xlsx');
		
		// Enhanced data preparation for Excel with structured output support
		const worksheetData = [
			['Prompt Name', 'Prompt', 'Response', 'Structured Output', 'Raw JSON', 'Schema Used', 'Status', 'Validation Error'] // Headers
		];
		
		checklistResults.forEach(result => {
			worksheetData.push([
				result.promptTitle || result.promptCommand || 'Untitled',
				result.prompt || '',
				result.response || '',
				result.structured_output ? 'Yes' : 'No',
				result.rawResponse || '',
				result.schema || '',
				result.error ? 'Error' : 'Success',
				result.validation_error || ''
			]);
		});
		
		// Create workbook and worksheet
		const workbook = XLSX.utils.book_new();
		const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
		
		// Enhanced column widths for structured output columns
		worksheet['!cols'] = [
			{ width: 25 }, // Prompt Name column
			{ width: 40 }, // Prompt column
			{ width: 60 }, // Response column
			{ width: 15 }, // Structured Output column
			{ width: 50 }, // Raw JSON column
			{ width: 40 }, // Schema Used column
			{ width: 12 }, // Status column
			{ width: 30 }  // Validation Error column
		];
		
		// Apply styling to headers
		const headerStyle = {
			font: { bold: true, color: { rgb: "FFFFFF" } },
			fill: { fgColor: { rgb: "4CAF50" } }
		};
		
		// Apply header styling (first row)
		for (let col = 0; col < worksheetData[0].length; col++) {
			const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
			if (!worksheet[cellAddress]) worksheet[cellAddress] = {};
			worksheet[cellAddress].s = headerStyle;
		}
		
		// Apply conditional formatting based on status
		checklistResults.forEach((result, index) => {
			const rowIndex = index + 1; // Skip header row
			const statusCol = 6; // Status column index
			const cellAddress = XLSX.utils.encode_cell({ r: rowIndex, c: statusCol });
			
			if (!worksheet[cellAddress]) worksheet[cellAddress] = {};
			
			if (result.error) {
				worksheet[cellAddress].s = {
					fill: { fgColor: { rgb: "FFEBEE" } },
					font: { color: { rgb: "D32F2F" }, bold: true }
				};
			} else if (result.structured_output) {
				worksheet[cellAddress].s = {
					fill: { fgColor: { rgb: "E8F5E8" } },
					font: { color: { rgb: "388E3C" }, bold: true }
				};
			}
		});
		
		// Add worksheet to workbook
		XLSX.utils.book_append_sheet(workbook, worksheet, 'Checklist Results');
		
		// Generate file
		const timestamp = generateTimestampUID();
		const defaultFilename = filename || `checklist-results-${timestamp}.xlsx`;
		
		// Write and download file
		XLSX.writeFile(workbook, defaultFilename);
		
	} catch (error) {
		console.error('Error exporting to XLSX:', error);
		// Fallback to simple Excel export
		exportToExcel(checklistResults, filename);
	}
};

/**
 * Generate a unique timestamp identifier for filenames
 */
const generateTimestampUID = (): string => {
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, '0');
	const day = String(now.getDate()).padStart(2, '0');
	const hours = String(now.getHours()).padStart(2, '0');
	const minutes = String(now.getMinutes()).padStart(2, '0');
	const seconds = String(now.getSeconds()).padStart(2, '0');
	
	return `${year}${month}${day}-${hours}${minutes}${seconds}`;
};

/**
 * Helper function to trigger file download
 */
const downloadFile = (content: string, filename: string, mimeType: string): void => {
	const blob = new Blob([content], { type: mimeType });
	const url = window.URL.createObjectURL(blob);
	
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	link.style.display = 'none';
	
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	
	// Clean up the URL object
	window.URL.revokeObjectURL(url);
};

/**
 * Helper function to escape HTML entities
 */
const escapeHtml = (text: string): string => {
	const div = document.createElement('div');
	div.textContent = text;
	return div.innerHTML;
};

/**
 * Get summary statistics for checklist results
 */
export const getChecklistStats = (checklistResults: ChecklistResult[]): {
	total: number;
	errors: number;
	successful: number;
	structured: number;
	validationErrors: number;
} => {
	const total = checklistResults.length;
	const errors = checklistResults.filter(r => r.error).length;
	const successful = total - errors;
	const structured = checklistResults.filter(r => r.structured_output).length;
	const validationErrors = checklistResults.filter(r => r.validation_error).length;
	
	return { total, errors, successful, structured, validationErrors };
};