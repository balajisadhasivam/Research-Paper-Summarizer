# Research Paper Summarizer

An educational tool that helps users understand research papers by providing simplified summaries at different reading levels and generating study flashcards.

## Features

- Summarize research paper abstracts
- Generate simplified versions for different reading levels (Beginner, Intermediate, Expert)
- Create study flashcards from key concepts
- Support for direct text input and arXiv paper links

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

## Project Structure

```
research_summarizer/
├── app/                    # Streamlit application
├── core/                   # Core processing logic
├── models/                 # Model management
└── requirements.txt        # Project dependencies
```

## Usage

1. Launch the application
2. Enter a research paper abstract or arXiv paper URL
3. Select desired reading level
4. View the simplified summary and flashcards

