"""
Response Parser for FAQBuddy Frontend
This module provides utilities for parsing LLM responses to separate thinking from main answers.
"""

import re
from typing import Dict, Any


def parse_response_with_thinking(response: str) -> Dict[str, Any]:
    """
    Parse the LLM response to separate thinking from main answer.
    This is used by the frontend to show/hide the thinking section.
    
    Args:
        response: Full response from the LLM
        
    Returns:
        Dictionary with 'thinking', 'main_answer', 'full_response', and 'has_thinking' keys
    """
    if not response:
        return {
            'thinking': '',
            'main_answer': '',
            'full_response': '',
            'has_thinking': False
        }
    
    # Look for the thinking section with multiple patterns
    thinking_patterns = [
        r'🤔\s*\*\*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)',
        r'🤔\s*Thinking(.*?)(?=\n\n\*\*Risposta\*\*)',
        r'\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)',
        r'THINKING.*?(?=\n\n\*\*Risposta\*\*)',
        r'RAGIONAMENTO.*?(?=\n\n\*\*Risposta\*\*)'
    ]
    
    thinking_content = ""
    main_answer = response  # Default to full response if no structure found
    has_thinking = False
    
    for pattern in thinking_patterns:
        thinking_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if thinking_match:
            thinking_content = thinking_match.group(1).strip()
            has_thinking = True
            # Extract the main answer part
            main_answer_match = re.search(r'\*\*Risposta\*\*(.*)', response, re.DOTALL | re.IGNORECASE)
            if main_answer_match:
                main_answer = main_answer_match.group(1).strip()
            break
    
    # If no thinking section found, try to extract from the beginning
    if not thinking_content:
        # Look for any thinking-like content at the beginning
        thinking_start_patterns = [
            r'^(.*?)(?=\n\n\*\*Risposta\*\*)',
            r'^(.*?)(?=\n\nRisposta)',
            r'^(.*?)(?=\n\n##)',
            r'^(.*?)(?=\n\n#)'
        ]
        
        for pattern in thinking_start_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match and len(match.group(1).strip()) > 50:  # Only if substantial content
                thinking_content = match.group(1).strip()
                has_thinking = True
                # Remove thinking from main answer
                main_answer = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE).strip()
                break
    
    # Clean up the main answer
    main_answer = re.sub(r'^Risposta:\s*', '', main_answer, flags=re.IGNORECASE)
    main_answer = re.sub(r'^Answer:\s*', '', main_answer, flags=re.IGNORECASE)
    main_answer = re.sub(r'^Response:\s*', '', main_answer, flags=re.IGNORECASE)
    
    return {
        'thinking': thinking_content,
        'main_answer': main_answer,
        'full_response': response,
        'has_thinking': has_thinking
    }


def format_response_for_frontend(response: str) -> Dict[str, Any]:
    """
    Format the response for frontend display with collapsible thinking section.
    
    Args:
        response: Full response from the LLM
        
    Returns:
        Dictionary formatted for frontend consumption
    """
    parsed = parse_response_with_thinking(response)
    
    return {
        'display_answer': parsed['main_answer'],
        'thinking_content': parsed['thinking'],
        'show_thinking_button': parsed['has_thinking'],
        'full_response': parsed['full_response']
    }


def create_collapsible_html(thinking_content: str, main_answer: str) -> str:
    """
    Create HTML with collapsible thinking section for frontend display.
    
    Args:
        thinking_content: The thinking/reasoning content
        main_answer: The main answer content
        
    Returns:
        HTML string with collapsible thinking section
    """
    if not thinking_content:
        return main_answer
    
    # Generate unique ID for this collapsible section
    import uuid
    collapsible_id = f"thinking-{uuid.uuid4().hex[:8]}"
    
    html = f"""
    <div class="faqbuddy-response">
        <div class="main-answer">
            {main_answer}
        </div>
        
        <details class="thinking-section" id="{collapsible_id}">
            <summary class="thinking-toggle">
                🤔 Mostra il ragionamento
            </summary>
            <div class="thinking-content">
                {thinking_content}
            </div>
        </details>
    </div>
    """
    
    return html


def create_markdown_with_collapsible(thinking_content: str, main_answer: str) -> str:
    """
    Create Markdown with collapsible thinking section using HTML details/summary.
    
    Args:
        thinking_content: The thinking/reasoning content
        main_answer: The main answer content
        
    Returns:
        Markdown string with HTML collapsible section
    """
    if not thinking_content:
        return main_answer
    
    # Generate unique ID for this collapsible section
    import uuid
    collapsible_id = f"thinking-{uuid.uuid4().hex[:8]}"
    
    markdown = f"""
{main_answer}

<details class="thinking-section" id="{collapsible_id}">
<summary class="thinking-toggle">🤔 Mostra il ragionamento</summary>

{thinking_content}

</details>
"""
    
    return markdown.strip()
