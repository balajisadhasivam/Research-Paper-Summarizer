import torch
import logging
from typing import List, Dict, Any
import numpy as np
from transformers import PreTrainedTokenizer, PreTrainedModel

def get_device_info() -> Dict[str, Any]:
    """
    Get information about available devices.
    
    Returns:
        Dict[str, Any]: Dictionary containing device information
    """
    info = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "current_device": torch.cuda.current_device() if torch.cuda.is_available() else None,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    }
    return info

def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage.
    
    Returns:
        Dict[str, float]: Dictionary containing memory usage information
    """
    if torch.cuda.is_available():
        memory_allocated = torch.cuda.memory_allocated() / 1024**2  # MB
        memory_reserved = torch.cuda.memory_reserved() / 1024**2  # MB
        return {
            "allocated_mb": memory_allocated,
            "reserved_mb": memory_reserved
        }
    return {
        "allocated_mb": 0.0,
        "reserved_mb": 0.0
    }

def optimize_memory():
    """Clear CUDA cache and optimize memory usage."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

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

def calculate_text_complexity(text: str) -> float:
    """
    Calculate text complexity score.
    
    Args:
        text (str): Input text
        
    Returns:
        float: Complexity score between 0 and 1
    """
    # Simple complexity metrics
    sentences = text.split('.')
    words = text.split()
    
    if not sentences or not words:
        return 0.0
    
    avg_sentence_length = len(words) / len(sentences)
    avg_word_length = np.mean([len(word) for word in words])
    
    # Normalize metrics
    sentence_score = min(avg_sentence_length / 20, 1.0)
    word_score = min(avg_word_length / 10, 1.0)
    
    # Combine scores
    complexity = (sentence_score + word_score) / 2
    return min(max(complexity, 0.0), 1.0)

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