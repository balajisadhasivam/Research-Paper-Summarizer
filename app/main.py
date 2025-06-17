import streamlit as st
import sys
import os
import logging
from typing import Dict, Any, Callable

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.summarizer import ResearchSummarizer
from core.flashcard_gen import FlashcardGenerator
from models.model_loader import ModelManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_components() -> Dict[str, Any]:
    """Initialize core components (summarizer and flashcard_gen only)."""
    return {
        "summarizer": ResearchSummarizer(),
        "flashcard_gen": FlashcardGenerator()
    }

def process_text(text: str, components: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
    """
    Process the input text through all components, showing partial results and debug info in Streamlit.
    
    Args:
        text (str): Input text
        components (Dict[str, Any]): Core components
        progress_callback (Callable): Function to update progress
        
    Returns:
        Dict[str, Any]: Processing results (may be partial)
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    def update_progress(message: str, progress: float = None):
        status_text.text(message)
        if progress is not None:
            progress_bar.progress(progress)
    model_manager = ModelManager()
    model_manager.set_progress_callback(update_progress)
    results = {}
    # Step 1: Summarize
    try:
        update_progress("Generating summary...", 0.3)
        summary = components["summarizer"].summarize(text)
        results["summary"] = summary
        update_progress("Summary generated", 0.6)
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        results["summary"] = None
    # Step 2: Generate flashcards
    try:
        update_progress("Generating flashcards...", 0.9)
        flashcards = components["flashcard_gen"].generate_flashcards(results["summary"])
        results["flashcards"] = flashcards
        update_progress("Processing complete!", 1.0)
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        results["flashcards"] = []
    return results

def main():
    st.set_page_config(
        page_title="Research Paper Summarizer",
        page_icon="📚",
        layout="wide"
    )

    st.title("📚 Research Paper Summarizer")
    st.markdown("""
    Summarize research papers and generate study flashcards instantly.
    """)

    # Initialize components
    components = {
        "summarizer": ResearchSummarizer(),
        "flashcard_gen": FlashcardGenerator()
    }

    # Input section
    st.header("Input")
    input_type = st.radio(
        "Choose input type:",
        ["Text Input", "arXiv URL"]
    )

    if input_type == "Text Input":
        text_input = st.text_area(
            "Paste your research paper abstract here:",
            height=200,
            help="Enter the text you want to summarize and analyze."
        )
    else:
        arxiv_url = st.text_input(
            "Enter arXiv paper URL:",
            help="Enter the URL of an arXiv paper (e.g., https://arxiv.org/abs/1234.5678)"
        )

    # Process button
    if st.button("Generate Summary & Flashcards", type="primary"):
        if input_type == "Text Input" and text_input:
            with st.spinner("Processing..."):
                try:
                    results = process_text(text_input, components, st.progress)
                    # Results section
                    st.header("Results")
                    # Create tabs for different outputs
                    tab1, tab2 = st.tabs(["Summary", "Flashcards"])
                    with tab1:
                        st.subheader("Summary")
                        st.write(results["summary"])
                    with tab2:
                        st.subheader("Study Flashcards")
                        for i, card in enumerate(results["flashcards"], 1):
                            if "question" in card and "answer" in card:
                                with st.expander(f"Card {i}"):
                                    st.write("**Question:**")
                                    st.write(card["question"])
                                    st.write("**Answer:**")
                                    st.write(card["answer"])
                except Exception as e:
                    st.error(f"An error occurred while processing the text: {str(e)}")
        elif input_type == "arXiv URL" and arxiv_url:
            with st.spinner("Fetching and processing paper..."):
                st.info("arXiv processing is not yet implemented.")
        else:
            st.warning("Please provide input text or a valid arXiv URL.")

if __name__ == "__main__":
    main() 