from typing import List, Dict, Any
import logging
from models.model_loader import ModelManager
from models.config import MODEL_CONFIGS, FLASHCARD_SETTINGS
from models.utils import chunk_text, format_model_output

class FlashcardGenerator:
    def __init__(self):
        self.model_manager = ModelManager()
        self.config = MODEL_CONFIGS["flashcard_gen"]
        self.settings = FLASHCARD_SETTINGS

    def _generate_flashcard_prompt(self, text: str, num_cards: int = 3) -> str:
        """Generate prompt for flashcard creation with explicit instructions and example."""
        return f"""Create {num_cards} flashcards from the following text. Format each flashcard as:
Question: [your question here]
Answer: [your answer here]

Example:
Question: What is semantic communication?
Answer: Semantic communication is a paradigm that focuses on the meaning of information exchanged in communication systems.

Text: {text}
"""

    def _clean_text(self, s: str) -> str:
        import re
        # Remove markdown, arrows, extra symbols, apologies, and meta-comments
        s = re.sub(r'[>*]+', '', s)
        s = re.sub(r'\*+', '', s)
        s = s.replace('**', '').replace('>>', '').replace('>', '').replace('<', '')
        lines = s.splitlines()
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
        return ' '.join(cleaned).strip()

    def generate_flashcards(self, text: str, num_cards: int = None) -> List[Dict[str, str]]:
        try:
            model, _ = self.model_manager.get_model("flashcard_gen")
            if num_cards is None:
                num_cards = self.settings["default_num_cards"]
            chunks = chunk_text(text, self.config["max_length"])
            flashcards = []
            seen_qas = set()
            remaining_cards = num_cards
            raw_outputs = []  # For debugging
            for i, chunk in enumerate(chunks):
                if remaining_cards <= 0:
                    break
                cards_to_generate = min(
                    remaining_cards,
                    self.settings["max_cards_per_request"]
                )
                prompt = self._generate_flashcard_prompt(chunk, cards_to_generate)
                logging.info(f"[FlashcardGen] Requesting {cards_to_generate} cards for chunk {i+1}/{len(chunks)}")
                flashcard_text = model(prompt)
                raw_outputs.append(flashcard_text)
                if not flashcard_text:
                    logging.warning(f"[FlashcardGen] Model returned empty string for chunk flashcards. Skipping chunk. Chunk: {chunk[:100]}...")
                    continue # Skip empty chunks
                logging.info(f"[FlashcardGen] Raw model output: {flashcard_text[:500]}")
                try:
                    card_texts = flashcard_text.split("Question:")[1:]
                    if not card_texts:
                        logging.warning(f"[FlashcardGen] No 'Question:' found in raw output for chunk. Raw: {flashcard_text[:100]}...")
                        continue
                    for card_text in card_texts:
                        if "Answer:" in card_text:
                            question, answer = card_text.split("Answer:", 1)
                            question = self._clean_text(question)
                            answer = self._clean_text(answer)
                            if not question or not answer:
                                logging.warning(f"[FlashcardGen] Empty question or answer after cleaning. Skipping card. Raw Q: {question[:50]}, Raw A: {answer[:50]}")
                                continue
                            qa_pair = (question.lower(), answer.lower())
                            if qa_pair in seen_qas:
                                logging.info(f"[FlashcardGen] Skipping duplicate flashcard: Q: {question}")
                                continue  # Skip duplicates
                            logging.info(f"[FlashcardGen] Cleaned Q: {question} | Cleaned A: {answer}")
                            # Relaxed filtering for debugging: allow shorter Q/A
                            flashcards.append({
                                "question": format_model_output(question, self.settings["max_question_length"]),
                                "answer": format_model_output(answer, self.settings["max_answer_length"])
                            })
                            seen_qas.add(qa_pair)
                            remaining_cards -= 1
                            if remaining_cards <= 0:
                                break
                except Exception as e:
                    logging.warning(f"[FlashcardGen] Error parsing flashcard: {str(e)} | Raw: {flashcard_text[:200]}...")
                    continue
            if not flashcards and text:
                logging.warning("No flashcards generated from chunks, trying with the whole text as fallback.")
                prompt = self._generate_flashcard_prompt(text, num_cards)
                flashcard_text = model(prompt)
                raw_outputs.append(flashcard_text)
                if not flashcard_text:
                    logging.error("[FlashcardGen] Fallback model call returned empty string.")
                    return [] # Return empty list if fallback fails
                logging.info(f"[FlashcardGen] Raw model output: {flashcard_text[:500]}")
                try:
                    card_texts = flashcard_text.split("Question:")[1:]
                    if not card_texts:
                        logging.warning(f"[FlashcardGen] No 'Question:' found in fallback raw output. Raw: {flashcard_text[:100]}...")
                        return []
                    for card_text in card_texts:
                        if "Answer:" in card_text:
                            question, answer = card_text.split("Answer:", 1)
                            question = self._clean_text(question)
                            answer = self._clean_text(answer)
                            if not question or not answer:
                                logging.warning(f"[FlashcardGen] Empty question or answer in fallback after cleaning. Skipping card.")
                                continue
                            qa_pair = (question.lower(), answer.lower())
                            if qa_pair in seen_qas:
                                logging.info(f"[FlashcardGen] Skipping duplicate flashcard in fallback: Q: {question}")
                                continue
                            logging.info(f"[FlashcardGen] Cleaned Q: {question} | Cleaned A: {answer}")
                            flashcards.append({
                                "question": format_model_output(question, self.settings["max_question_length"]),
                                "answer": format_model_output(answer, self.settings["max_answer_length"])
                            })
                            seen_qas.add(qa_pair)
                except Exception as e:
                    logging.error(f"[FlashcardGen] Fallback flashcard parse error: {str(e)} | Raw: {flashcard_text[:200]}...")
            # For debugging: if no flashcards, return raw outputs
            if not flashcards:
                return [{"raw_output": ro} for ro in raw_outputs]
            return flashcards
        except Exception as e:
            logging.error(f"Error generating flashcards: {str(e)}")
            return [] # Return empty list on top-level error

    def format_flashcards(self, flashcards: List[Dict[str, str]]) -> str:
        """
        Format flashcards for display.
        
        Args:
            flashcards (List[Dict[str, str]]): List of flashcards
            
        Returns:
            str: Formatted flashcard text
        """
        formatted_text = ""
        for i, card in enumerate(flashcards, 1):
            formatted_text += f"Card {i}:\n"
            formatted_text += f"Q: {card['question']}\n"
            formatted_text += f"A: {card['answer']}\n\n"
        return formatted_text 