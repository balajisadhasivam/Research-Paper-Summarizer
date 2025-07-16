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
        Generate a concise summary of the input text, followed by a single bulleted list of key highlights with bolded phrases. Remove any XML-style tags from the output. Only keep the first summary and the first highlights section.
        Handles long inputs by chunking, summarizing each chunk, and then summarizing the combined summaries.
        """
        from models.utils import chunk_text
        try:
            model, _ = self.model_manager.get_model("summarizer")
            # Chunk the input text if it's too long
            chunks = chunk_text(text, max_length=2000)
            chunk_summaries = []
            if len(chunks) == 1:
                prompt = (
                    "Write ONLY the following two sections for the text below:\n"
                    "Summary: [Write a single, concise paragraph summarizing the main research question, methodology, findings, and implications. Do not include any section headers, meta-comments, or repeated information.]\n"
                    "Key Highlights: [After the summary, write exactly one section titled 'Key Highlights:' on a new line, followed by 2-4 bullet points. Each bullet should begin with a bolded label (e.g., **Novelty:**, **Findings:**, **Implication:**) and be concise, non-redundant, and directly related to the main contributions or results.]\n"
                    "Do not repeat information between the summary and highlights. Do not continue writing after the highlights section. Do not include any XML, HTML, or markdown other than bold for the highlight labels. Only output the summary and the 'Key Highlights:' section, nothing else.\n\n"
                    f"{text}"
                )
                logging.info(f"[Summarizer] Prompt sent to model: {prompt[:300]}... (length: {len(prompt)})")
                raw_output = model(prompt)
                chunk_summaries.append(raw_output)
            else:
                # Summarize each chunk
                for idx, chunk in enumerate(chunks):
                    prompt = (
                        f"Summarize the following part of a research paper (part {idx+1} of {len(chunks)}):\n\n{chunk}"
                    )
                    logging.info(f"[Summarizer] Chunk {idx+1}/{len(chunks)} prompt sent to model: {prompt[:300]}... (length: {len(prompt)})")
                    chunk_summary = model(prompt)
                    chunk_summaries.append(chunk_summary)
                # Combine all chunk summaries and summarize again for final output
                combined = '\n'.join(chunk_summaries)
                final_prompt = (
                    "Write ONLY the following two sections for the text below (which is a set of summaries of a research paper):\n"
                    "Summary: [Write a single, concise paragraph summarizing the main research question, methodology, findings, and implications. Do not include any section headers, meta-comments, or repeated information.]\n"
                    "Key Highlights: [After the summary, write exactly one section titled 'Key Highlights:' on a new line, followed by 2-4 bullet points. Each bullet should begin with a bolded label (e.g., **Novelty:**, **Findings:**, **Implication:**) and be concise, non-redundant, and directly related to the main contributions or results.]\n"
                    "Do not repeat information between the summary and highlights. Do not continue writing after the highlights section. Do not include any XML, HTML, or markdown other than bold for the highlight labels. Only output the summary and the 'Key Highlights:' section, nothing else.\n\n"
                    f"{combined}"
                )
                logging.info(f"[Summarizer] Final combining prompt sent to model: {final_prompt[:300]}... (length: {len(final_prompt)})")
                raw_output = model(final_prompt)
            import re
            # Remove XML/HTML tags
            raw_output = re.sub(r'<.*?>', '', raw_output)
            # Extract only the first 'Summary:' and 'Key Highlights:' sections
            summary = ''
            highlights = []
            in_summary = False
            in_highlights = False
            for line in raw_output.splitlines():
                l = line.strip()
                if not l:
                    continue
                if re.match(r"(?i)(the summary should|no, start with|here is a possible|please provide|i apologize|this is not|waiting for your text|now create|only output|summarize the following|do not include|output the summary|output only|in summary:|rewritten response is:)", l):
                    continue
                if l.startswith('```') or l.startswith('---'):
                    continue
                if l.lower().startswith('summary:'):
                    in_summary = True
                    in_highlights = False
                    continue
                if l.lower().startswith('key highlights:'):
                    in_highlights = True
                    in_summary = False
                    continue
                if in_highlights:
                    if l.startswith('*') or l.startswith('-') or l.startswith('•'):
                        highlights.append(l)
                        if len(highlights) >= 4:
                            break
                    else:
                        # Stop if we hit a new section or text after highlights
                        break
                elif in_summary:
                    summary += (l + ' ')
            summary = summary.strip()
            if highlights:
                return f"Summary:\n{summary}\n\nKey Highlights:\n" + '\n'.join(highlights)
            else:
                return summary
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