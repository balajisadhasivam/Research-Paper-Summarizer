from typing import List

def chunk_text(text: str, max_length: int = 2000) -> List[str]:
    """
    Split text into chunks of maximum length, trying to keep paragraphs together.
    
    Args:
        text (str): Input text
        max_length (int): Maximum length of each chunk
        
    Returns:
        List[str]: List of text chunks
    """
    # Split into paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If a single paragraph is too long, split it into sentences
        if len(paragraph) > max_length:
            sentences = paragraph.split('. ')
            for sentence in sentences:
                if current_length + len(sentence) + 2 <= max_length:
                    current_chunk.append(sentence)
                    current_length += len(sentence) + 2
                else:
                    if current_chunk:
                        chunks.append('. '.join(current_chunk) + '.')
                    current_chunk = [sentence]
                    current_length = len(sentence)
        else:
            if current_length + len(paragraph) + 2 <= max_length:
                current_chunk.append(paragraph)
                current_length += len(paragraph) + 2
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = len(paragraph)
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def format_model_output(output: str, max_length: int = None) -> str:
    """
    Format model output for display.
    
    Args:
        output (str): Model output text
        max_length (int, optional): Maximum length of formatted output
        
    Returns:
        str: Formatted output text
    """
    # Remove extra whitespace
    output = " ".join(output.split())
    
    # Truncate if needed
    if max_length and len(output) > max_length:
        output = output[:max_length] + "..."
    
    return output 