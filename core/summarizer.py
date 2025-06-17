from typing import Optional, Dict, Any
import logging
from models.model_loader import ModelManager
from models.config import MODEL_CONFIGS
from models.utils import chunk_text, format_model_output

class ResearchSummarizer:
    def __init__(self):
        self.model_manager = ModelManager()
        self.config = MODEL_CONFIGS["summarizer"]

    def summarize(self, text: str, max_length: int = 150) -> str:
        """
        Generate a summary of the input text using the exact playground prompt. Only minimal cleaning.
        """
        try:
            model, _ = self.model_manager.get_model("summarizer")
            prompt = (
                "Summarize the following text as an academic abstract. "
                "Focus on the main research question, methodology, findings, and implications. "
                "Use clear, concise language.\n\n"
                f"{text}"
            )
            logging.info(f"[Summarizer] Prompt sent to model: {prompt[:300]}... (length: {len(prompt)})")
            raw_output = model(prompt)
            # Minimal cleaning: remove apologies/meta-comments, join lines
            import re
            lines = raw_output.splitlines()
            cleaned = []
            for line in lines:
                l = line.strip()
                if not l:
                    continue
                if re.match(r"(?i)(the summary should|no, start with|here is a possible|please provide|i apologize|this is not|waiting for your text|now create|only output|summarize the following|do not include|output the summary|output only|in summary:|rewritten response is:)", l):
                    continue
                if l.startswith('```') or l.startswith('---'):
                    continue
                cleaned.append(l)
            return ' '.join(cleaned) if cleaned else raw_output.strip()
        except Exception as e:
            logging.error(f"Error generating summary: {str(e)}")
            return f"[DEBUG] Error: {str(e)}"

    def process_arxiv_paper(self, arxiv_id: str) -> Dict[str, Any]:
        """
        Process an arXiv paper and return its summary.
        
        Args:
            arxiv_id (str): arXiv paper ID
            
        Returns:
            Dict[str, Any]: Dictionary containing paper information and summary
        """
        # TODO: Implement arXiv paper processing
        pass 