/**
 * Utility functions for formatting source displays with original path information.
 */

/**
 * Check if a file path is a temporary file path.
 * @param {string} filePath - File path to check
 * @returns {boolean} True if it's a temp file path, False otherwise
 */
export function isTempFilePath(filePath) {
    if (!filePath) return false;
    
    const tempIndicators = [
        'Temp',
        'tmp',
        '/tmp/',
        '\\temp\\',
        'tempfile',
        'temp_file'
    ];
    
    const filePathLower = filePath.toLowerCase();
    return tempIndicators.some(indicator => 
        filePathLower.includes(indicator.toLowerCase())
    );
}

/**
 * Get the best available original filename from a source.
 * @param {Object} source - Source object containing metadata
 * @returns {string|null} Original filename if available, null otherwise
 */
export function getOriginalFilename(source) {
    // Priority order for original filename
    const filenameOptions = [
        source.original_filename,
        source.original_name,
        source.display_name,
        source.filename
    ];
    
    // First try to find a non-temp file
    for (const option of filenameOptions) {
        if (option && !isTempFilePath(option)) {
            return option;
        }
    }
    
    // If all options are temp files or null, return the first non-null option
    for (const option of filenameOptions) {
        if (option) {
            return option;
        }
    }
    
    return null;
}

/**
 * Format a source for display, prioritizing original file information.
 * @param {Object} source - Source object containing metadata
 * @returns {string} Formatted string for display
 */
export function formatSourceDisplay(source) {
    // Get the best available original file information
    let originalFile = source.original_filename || 
                      source.original_name || 
                      source.display_name || 
                      source.filename || 
                      source.file_path || '';
    
    if (!originalFile) {
        // Fallback to extracting filename from path
        const filePath = source.file_path || '';
        if (filePath) {
            originalFile = filePath.split(/[/\\]/).pop() || 'Unknown Source';
        } else {
            originalFile = 'Unknown Source';
        }
    }
    
    // Check if this is a temp file
    const isTemp = isTempFilePath(originalFile);
    
    // If it's a temp file, try to get the original name
    if (isTemp) {
        const originalName = source.original_name || source.display_name;
        if (originalName) {
            originalFile = originalName;
        }
    }
    
    // Format the display
    if (originalFile.includes('/') || originalFile.includes('\\')) {
        // For full paths, show a shortened version
        const pathParts = originalFile.replace(/\\/g, '/').split('/');
        if (pathParts.length > 3) {
            const displayPath = `.../${pathParts.slice(-3).join('/')}`;
            return `📄 **${displayPath}**`;
        } else {
            return `📄 **${originalFile}**`;
        }
    } else {
        return `📄 **${originalFile}**`;
    }
}

/**
 * Get source metadata summary.
 * @param {Object} source - Source object containing metadata
 * @returns {Object} Dictionary with key metadata fields
 */
export function getSourceMetadataSummary(source) {
    return {
        original_filename: source.original_filename,
        original_name: source.original_name,
        display_name: source.display_name,
        file_path: source.file_path,
        filename: source.filename,
        upload_source: source.upload_source,
        upload_timestamp: source.upload_timestamp,
        is_temp_file: source.is_temp_file || false,
        source_type: source.source_type,
        doc_id: source.doc_id,
        chunk_id: source.chunk_id
    };
}

/**
 * Format a search result for frontend display with enhanced source information.
 * @param {Object} result - Raw search result from query engine
 * @returns {Object} Formatted result for display
 */
export function formatSearchResultForDisplay(result) {
    // Extract source information
    const sourceInfo = getSourceMetadataSummary(result);
    
    // Format the display
    const formattedResult = {
        content: result.text || '',
        score: result.similarity_score || 0,
        source_display: formatSourceDisplay(result),
        source_info: sourceInfo,
        metadata: result.metadata || {},
        doc_id: result.doc_id,
        chunk_id: result.chunk_id
    };
    
    return formattedResult;
}

/**
 * Upload file with original path information.
 * @param {File} file - File to upload
 * @param {string} originalPath - Original file path (optional)
 * @param {string} description - Additional description (optional)
 * @param {string} uploadSource - Source of the upload (default: web_upload)
 * @param {Object} additionalMetadata - Additional metadata object (optional)
 * @returns {Promise<Object>} Upload response
 */
export async function uploadFileWithOriginalPath(file, originalPath = null, description = null, uploadSource = 'web_upload', additionalMetadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Include the original file path if available
    if (originalPath) {
        formData.append('original_path', originalPath);
    } else {
        // Use the file name as fallback
        formData.append('original_path', file.name);
    }
    
    // Add optional fields
    if (description) {
        formData.append('description', description);
    }
    
    if (uploadSource) {
        formData.append('upload_source', uploadSource);
    }
    
    if (Object.keys(additionalMetadata).length > 0) {
        formData.append('additional_metadata', JSON.stringify(additionalMetadata));
    }
    
    const response = await fetch('/api/upload/enhanced', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
}

/**
 * Format search results for display with enhanced source information.
 * @param {Array} results - Array of search results
 * @returns {Array} Formatted results for display
 */
export function formatSearchResultsForDisplay(results) {
    return results.map(result => formatSearchResultForDisplay(result));
}

/**
 * Create a source label for display in search results.
 * @param {Object} source - Source object
 * @param {number} index - Index of the source
 * @returns {string} Formatted source label
 */
export function createSourceLabel(source, index) {
    const originalFile = getOriginalFilename(source);
    
    if (originalFile) {
        // If it's a full path, show just the filename
        if (originalFile.includes('/') || originalFile.includes('\\')) {
            const fileName = originalFile.split(/[/\\]/).pop();
            return fileName || `Source ${index + 1}`;
        }
        return originalFile;
    }
    
    return `Source ${index + 1}`;
} 