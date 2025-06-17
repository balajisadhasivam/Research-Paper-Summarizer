import os
from typing import Dict, Any

# API Configuration
API_CONFIG = {
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "models": {
            "summarizer": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "level_adapter": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "flashcard_gen": "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        },
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "rate_limit": {
            "requests_per_minute": 60,
            "min_interval": 1.0  # Minimum seconds between requests
        }
    }
}

# Model-specific configurations
MODEL_CONFIGS = {
    "summarizer": {
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "max_length": 2048,
        "min_length": 100,
        "system_prompt": """You are an expert research paper summarizer. Your task is to create clear, concise, and accurate summaries of academic papers. Focus on:
1. Main research question and objectives
2. Key methodology and approach
3. Major findings and conclusions
4. Important implications and contributions

Format the summary in a structured way with clear sections."""
    },
    
    "level_adapter": {
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "max_length": 2048,
        "min_length": 100,
        "system_prompt": """You are an expert at adapting academic text to different reading levels. Your task is to rewrite text to be more accessible while maintaining accuracy and key concepts. Consider:
1. Vocabulary complexity
2. Sentence structure
3. Technical detail level
4. Overall readability

Maintain the original meaning while making the content more accessible."""
    },
    
    "flashcard_gen": {
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "max_length": 2048,
        "min_length": 50,
        "system_prompt": """You are an expert at creating educational flashcards from academic content. Your task is to generate clear, focused flashcards that:
1. Test key concepts and definitions
2. Cover important relationships and processes
3. Include both basic and advanced concepts
4. Are clear and unambiguous

Format each flashcard with a clear question and concise answer."""
    }
}

# Text processing settings
TEXT_SETTINGS = {
    "max_chunk_size": 2000,
    "overlap_size": 200,
    "min_chunk_size": 500
}

# Flashcard settings
FLASHCARD_SETTINGS = {
    "default_num_cards": 5,  # Default number of flashcards to generate
    "max_question_length": 150,
    "max_answer_length": 300,
    "min_question_length": 20,
    "min_answer_length": 30,
    "max_cards_per_request": 3  # Maximum number of cards to generate in one API call
}

# Level adaptation settings
LEVEL_SETTINGS = {
    "levels": ["beginner", "intermediate", "advanced"],
    "default_level": "intermediate"
}

# Reading level configurations
READING_LEVELS = {
    "Beginner": {
        "max_sentence_length": 15,
        "max_word_length": 8,
        "complexity_threshold": 0.3
    },
    "Intermediate": {
        "max_sentence_length": 25,
        "max_word_length": 12,
        "complexity_threshold": 0.6
    },
    "Expert": {
        "max_sentence_length": 35,
        "max_word_length": 20,
        "complexity_threshold": 0.9
    }
}

# Cache settings
CACHE_SETTINGS = {
    "max_cache_size": 2 * 1024 * 1024 * 1024,  # 2GB
    "cache_ttl": 3600,  # 1 hour
    "cleanup_interval": 300  # 5 minutes
} 