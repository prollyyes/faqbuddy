/**
 * Response Parser for FAQBuddy Frontend
 * This module provides utilities for parsing LLM responses to separate thinking from main answers.
 */

/**
 * Parse the LLM response to separate thinking from main answer.
 * This is used by the frontend to show/hide the thinking section.
 * 
 * @param {string} response - Full response from the LLM
 * @returns {Object} Dictionary with 'thinking', 'main_answer', 'full_response', and 'has_thinking' keys
 */
export function parseResponseWithThinking(response) {
    if (!response) {
        return {
            thinking: '',
            main_answer: '',
            full_response: '',
            has_thinking: false
        };
    }
    
    // Look for the thinking section with multiple patterns
    const thinkingPatterns = [
        /🤔\s*\*\*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)/s,
        /🤔\s*Thinking(.*?)(?=\n\n\*\*Risposta\*\*)/s,
        /\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)/s,
        /THINKING.*?(?=\n\n\*\*Risposta\*\*)/s,
        /RAGIONAMENTO.*?(?=\n\n\*\*Risposta\*\*)/s
    ];
    
    let thinkingContent = "";
    let mainAnswer = response; // Default to full response if no structure found
    let hasThinking = false;
    
    for (const pattern of thinkingPatterns) {
        const thinkingMatch = response.match(pattern);
        if (thinkingMatch) {
            thinkingContent = thinkingMatch[1].trim();
            hasThinking = true;
            // Extract the main answer part
            const mainAnswerMatch = response.match(/\*\*Risposta\*\*(.*)/s);
            if (mainAnswerMatch) {
                mainAnswer = mainAnswerMatch[1].trim();
            }
            break;
        }
    }
    
    // If no thinking section found, try to extract from the beginning
    if (!thinkingContent) {
        // Look for any thinking-like content at the beginning
        const thinkingStartPatterns = [
            /^(.*?)(?=\n\n\*\*Risposta\*\*)/s,
            /^(.*?)(?=\n\nRisposta)/s,
            /^(.*?)(?=\n\n##)/s,
            /^(.*?)(?=\n\n#)/s
        ];
        
        for (const pattern of thinkingStartPatterns) {
            const match = response.match(pattern);
            if (match && match[1].trim().length > 50) { // Only if substantial content
                thinkingContent = match[1].trim();
                hasThinking = true;
                // Remove thinking from main answer
                mainAnswer = response.replace(pattern, '').trim();
                break;
            }
        }
    }
    
    // Clean up the main answer
    mainAnswer = mainAnswer.replace(/^Risposta:\s*/i, '');
    mainAnswer = mainAnswer.replace(/^Answer:\s*/i, '');
    mainAnswer = mainAnswer.replace(/^Response:\s*/i, '');
    
    return {
        thinking: thinkingContent,
        main_answer: mainAnswer,
        full_response: response,
        has_thinking: hasThinking
    };
}

/**
 * Format the response for frontend display with collapsible thinking section.
 * 
 * @param {string} response - Full response from the LLM
 * @returns {Object} Dictionary formatted for frontend consumption
 */
export function formatResponseForFrontend(response) {
    const parsed = parseResponseWithThinking(response);
    
    return {
        display_answer: parsed.main_answer,
        thinking_content: parsed.thinking,
        show_thinking_button: parsed.has_thinking,
        full_response: parsed.full_response
    };
}

/**
 * Clean response from unwanted artifacts while preserving the thinking structure.
 * 
 * @param {string} response - Raw response from the LLM
 * @returns {string} Cleaned response string with thinking and answer sections preserved
 */
export function cleanResponseWithThinking(response) {
    if (!response) {
        return response;
    }
    
    // Remove system instruction tags
    let cleaned = response
        .replace(/\[INST\].*?\[\/INST\]/gs, '')
        .replace(/\[\/INST\]/g, '')
        .replace(/\[INST\]/g, '')
        .replace(/\[CITAZIONE\]/g, '')
        .replace(/\[\/CITAZIONE\]/g, '')
        .replace(/\[FINE\]/g, '');
    
    // Clean up extra whitespace and newlines
    cleaned = cleaned.replace(/\n\s*\n\s*\n/g, '\n\n'); // Replace multiple newlines with double newlines
    cleaned = cleaned.trim();
    
    return cleaned;
}
