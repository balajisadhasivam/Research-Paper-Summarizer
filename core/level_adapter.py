from typing import Dict, Any
import logging
from models.model_loader import ModelManager
from models.config import MODEL_CONFIGS, READING_LEVELS
from models.utils import chunk_text, format_model_output, calculate_text_complexity

class LevelAdapter:
    def __init__(self):
        self.model_manager = ModelManager()
        self.config = MODEL_CONFIGS["level_adapter"]

    def _get_prompt(self, text: str, level: str) -> str:
        """Generate appropriate prompt based on reading level, with explicit instructions and example."""
        prompts = {
            "Beginner": f"Rewrite the following text for a beginner. ONLY output the rewritten text. Do NOT include instructions, apologies, or explanations.\n\nExample:\nOriginal: Quantum entanglement is a phenomenon where particles become linked and the state of one instantly influences the other, no matter the distance.\nBeginner: Sometimes, tiny things like particles can be connected so that when something happens to one, the other changes too, even if they're far apart.\n\nText: {text}",
            "Intermediate": f"Rewrite the following text for an intermediate reader. ONLY output the rewritten text. Do NOT include instructions, apologies, or explanations.\n\nExample:\nOriginal: Quantum entanglement is a phenomenon where particles become linked and the state of one instantly influences the other, no matter the distance.\nIntermediate: Quantum entanglement means that two particles can be connected in such a way that changing one will instantly affect the other, even if they are far apart.\n\nText: {text}",
            "Expert": f"Rewrite the following text for an expert. ONLY output the rewritten text. Do NOT include instructions, apologies, or explanations.\n\nExample:\nOriginal: Quantum entanglement is a phenomenon where particles become linked and the state of one instantly influences the other, no matter the distance.\nExpert: Quantum entanglement describes a nonlocal correlation between quantum systems, such that the measurement of one system's state instantaneously determines the state of its entangled partner, regardless of spatial separation.\n\nText: {text}"
        }
        return prompts.get(level, prompts["Intermediate"])

    def adapt_text(self, text: str, level: str) -> str:
        """
        Adapt the text to the specified reading level. If adaptation fails, show raw output for debugging.
        
        Args:
            text (str): Input text to adapt
            level (str): Target reading level ("Beginner", "Intermediate", or "Expert")
            
        Returns:
            str: Adapted text or raw outputs for debugging
        """
        def clean_adapted(output: str) -> str:
            import re
            # Remove XML-style tags like <rewritten_response>
            output = re.sub(r'<.*?>', '', output)

            lines = output.splitlines()
            cleaned = []
            for line in lines:
                l = line.strip()
                if not l:
                    continue
                if re.match(r"(?i)(the summary should|no, start with|here is a possible|please provide|i apologize|this is not|waiting for your text|now create|only output|summarize the following|do not include|output the summary|output only|in summary:|rewritten response is:|rest of the original text remains the same)", l):
                    continue
                if l.startswith('```') or l.startswith('---'):
                    continue
                cleaned.append(l)
            return cleaned[0] if cleaned else output.strip()

        try:
            model, _ = self.model_manager.get_model("level_adapter")
            
            # Split text into chunks if it's too long
            chunks = chunk_text(text, self.config["max_length"])
            adapted_chunks = []
            raw_outputs = []  # For debugging
            
            for chunk in chunks:
                prompt = self._get_prompt(chunk, level)
                adapted_text = model(prompt)
                raw_outputs.append(adapted_text)
                if not adapted_text:
                    logging.warning(f"[LevelAdapter] Model returned empty string for chunk adaptation. Skipping chunk. Chunk: {chunk[:100]}...")
                    continue # Skip empty chunks
                logging.info(f"[LevelAdapter] Raw model output: {adapted_text[:500]}")
                cleaned = clean_adapted(adapted_text)
                if not cleaned:
                    logging.warning(f"[LevelAdapter] Cleaned adapted chunk is empty after post-processing. Raw output might be unparsable. Raw: {adapted_text[:100]}...")
                    continue
                logging.info(f"[LevelAdapter] Cleaned output: {cleaned[:500]}")
                adapted_chunks.append(cleaned)
            
            if not adapted_chunks:
                logging.error("[LevelAdapter] All adapted chunks were empty. Returning raw outputs for debugging.")
                return "[DEBUG] Raw model outputs: " + str(raw_outputs)

            # Combine adapted chunks
            final_text = " ".join(adapted_chunks)
            
            # Verify complexity matches target level
            complexity = calculate_text_complexity(final_text)
            target_complexity = READING_LEVELS[level]["complexity_threshold"]
            
            if abs(complexity - target_complexity) > 0.2:
                logging.warning(f"Adapted text complexity ({complexity:.2f}) is not close to target ({target_complexity:.2f}) for level '{level}'. Returning best attempt.")
            
            return format_model_output(final_text)

        except Exception as e:
            logging.error(f"Error adapting text: {str(e)}")
            return f"[DEBUG] Error: {str(e)}"

    def get_key_concepts(self, text: str) -> Dict[str, Any]:
        """
        Extract key concepts from the text.
        
        Args:
            text (str): Input text
            
        Returns:
            Dict[str, Any]: Dictionary containing key concepts and their explanations
        """
        try:
            model, _ = self.model_manager.get_model("level_adapter")
            prompt = f"Extract the key concepts from this text and explain each one briefly: {text}"
            concepts_text = model(prompt)
            
            # Parse the concepts into a dictionary
            concepts = {}
            for line in concepts_text.split('\n'):
                if ':' in line:
                    concept, explanation = line.split(':', 1)
                    concepts[concept.strip()] = explanation.strip()
            
            return concepts
        except Exception as e:
            logging.error(f"Error extracting key concepts: {str(e)}")
            raise 