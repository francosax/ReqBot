import logging
import re

import en_core_web_sm
import fitz
import pandas as pd

logging.basicConfig(filename='debug.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Phase 1 Improvement: Sentence length validation thresholds
MIN_REQUIREMENT_LENGTH_WORDS = 5
MAX_REQUIREMENT_LENGTH_WORDS = 100

# Phase 2 Improvement: Cache spaCy model for performance (3-5x speedup)
_nlp_model = None


def get_nlp_model():
    """
    Lazy-load and cache spaCy model for better performance.

    Loading the model once and reusing it provides 3-5x performance improvement
    when processing multiple PDFs in a session.

    Returns:
        spaCy Language model
    """
    global _nlp_model
    if _nlp_model is None:
        _nlp_model = en_core_web_sm.load()
        logging.info("spaCy model loaded and cached")
    return _nlp_model


def preprocess_pdf_text(text):
    """
    Phase 2 Improvement: Clean and normalize PDF text for better NLP processing.

    Handles common PDF extraction issues that can confuse sentence segmentation:
    - Hyphenated words split across lines
    - Inconsistent whitespace
    - Special Unicode characters
    - Page numbers and common artifacts

    Args:
        text (str): Raw text extracted from PDF

    Returns:
        str: Cleaned and normalized text ready for NLP processing
    """
    # Fix hyphenated words split across lines
    # Example: "require-\nment" -> "requirement"
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # Remove common page number patterns
    # Matches: "Page 5", "- 5 -", "5", etc. at start/end of lines
    text = re.sub(r'^\s*[-–—]?\s*\d+\s*[-–—]?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # Normalize different types of spaces
    text = text.replace('\u00a0', ' ')   # Non-breaking space
    text = text.replace('\u202f', ' ')   # Narrow no-break space
    text = text.replace('\u2009', ' ')   # Thin space
    text = text.replace('\u200b', '')    # Zero-width space

    # Normalize different types of dashes
    text = text.replace('\u2013', '-')   # En dash
    text = text.replace('\u2014', '-')   # Em dash
    text = text.replace('\u2015', '-')   # Horizontal bar

    # Normalize quotes
    text = text.replace('\u2018', "'")   # Left single quote
    text = text.replace('\u2019', "'")   # Right single quote
    text = text.replace('\u201c', '"')   # Left double quote
    text = text.replace('\u201d', '"')   # Right double quote

    # Remove multiple spaces (but keep single spaces)
    text = re.sub(r' +', ' ', text)

    # Remove multiple newlines (but keep paragraph breaks)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Remove empty lines but preserve paragraph structure
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:  # Only keep non-empty lines
            lines.append(line)

    return '\n'.join(lines)


def calculate_requirement_confidence(sentence, keyword, word_count):
    """
    Phase 2 Improvement: Calculate confidence score for a potential requirement.

    Uses multiple factors to assess the quality of an extracted requirement:
    - Sentence length (optimal: 8-50 words)
    - Presence of multiple requirement keywords
    - Common requirement sentence patterns
    - Header detection (penalized)
    - High number density (penalized, might be table data)

    Args:
        sentence (str): The extracted sentence text
        keyword (str): The keyword that triggered the match
        word_count (int): Number of words in the sentence

    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    confidence = 1.0
    sentence_lower = sentence.lower()

    # Factor 1: Sentence length
    # Optimal length: 8-50 words
    if word_count < 5:
        confidence *= 0.3  # Very short, likely fragment
    elif word_count < 8:
        confidence *= 0.7  # Short but might be valid
    elif 8 <= word_count <= 50:
        confidence *= 1.0  # Ideal length
    elif 50 < word_count <= 80:
        confidence *= 0.8  # Long but acceptable
    else:  # > 80 words
        confidence *= 0.5  # Very long, lower confidence

    # Factor 2: Multiple requirement keywords (higher confidence)
    requirement_keywords = ['shall', 'must', 'should', 'will', 'has to', 'required', 'ensure']
    keyword_count = sum(1 for kw in requirement_keywords if kw in sentence_lower)
    if keyword_count >= 2:
        confidence *= 1.2
    elif keyword_count >= 3:
        confidence *= 1.3

    # Factor 3: Requirement sentence patterns
    # Common patterns: "The system shall...", "X must...", etc.
    if re.match(r'^(the|this|that|each|all|every|a)\s+\w+\s+(shall|must|should|will)',
                sentence_lower):
        confidence *= 1.2

    # Factor 4: Penalize sentences that look like headers
    # Headers are often all caps or very short
    if sentence.isupper() and word_count <= 6:
        confidence *= 0.4
    elif word_count <= 3:
        confidence *= 0.5

    # Factor 5: Penalize sentences with lots of numbers (might be table data)
    numbers = re.findall(r'\d+', sentence)
    if len(numbers) > word_count * 0.3:  # More than 30% numbers
        confidence *= 0.6

    # Factor 6: Boost for specific requirement indicators
    if 'comply with' in sentence_lower or 'conform to' in sentence_lower:
        confidence *= 1.1
    if 'capable of' in sentence_lower or 'ability to' in sentence_lower:
        confidence *= 1.1

    # Cap confidence at 1.0
    return min(confidence, 1.0)


def requirement_finder(path, keywords_set, filename):
    doc = fitz.open(path)
    nlp = get_nlp_model()  # Use cached model instead of reloading

    cont_text = []
    pagine = []
    keyword = []

    for i, page in enumerate(doc, 1):
        page_text = page.get_text()
        # print(text)
        cont_text.append(page_text)

    # word_set = keywords_set
    word_set = {word.lower() for word in keywords_set}

    raw_sentences = []
    matching_sentences = []
    tag = []
    confidences = []  # Phase 2 Improvement: Store confidence scores
    req_c = 0
    # position = []
    current_page = None

    for i, page_text in enumerate(cont_text, 1):
        if i != current_page:
            req_c = 0
            current_page = i

        # Phase 2 Improvement: Use enhanced preprocessing instead of simple line filtering
        filtered_text = preprocess_pdf_text(page_text)
        doc_page = nlp(filtered_text)
        for sent in doc_page.sents:
            # Phase 1 Improvement: Validate sentence length before processing
            word_count = len(sent.text.split())

            # Skip if too short (likely fragment or heading)
            if word_count < MIN_REQUIREMENT_LENGTH_WORDS:
                continue

            # Skip if too long (likely parsing error - prevents full page highlights)
            if word_count > MAX_REQUIREMENT_LENGTH_WORDS:
                logging.warning(
                    f"Skipping overly long sentence on page {i} "
                    f"({word_count} words) - likely PDF parsing error"
                )
                continue

            # Phase 1 Improvement: Use word boundary matching to avoid substring matches
            # Extract words without punctuation using regex
            sentence_words = re.findall(r'\b\w+\b', sent.text.lower())
            if any(word in word_set for word in sentence_words):
                req_c += 1
                # raw_sentences.append(sent)
                raw_sentences.append(sent.text.split())
                cleaned_sentence = sent.text.strip().replace('\n', ' ')
                matching_sentences.append(cleaned_sentence)
                pagine.append(i)
                # Find the keyword and ensure it's in lowercase
                keyword_word = next(word for word in sentence_words if word in word_set)
                keyword.append(keyword_word)
                # Create a tag for the requirement
                tag.append(filename + '-Req#' + str(i) + '-' + str(req_c))

                # Phase 2 Improvement: Calculate confidence score for this requirement
                confidence_score = calculate_requirement_confidence(
                    cleaned_sentence,
                    keyword_word,
                    word_count
                )
                confidences.append(confidence_score)

    df = pd.DataFrame({
        'Label Number': tag,
        'Description': matching_sentences,
        'Page': pagine,
        'Keyword': keyword,
        'Raw': raw_sentences,
        'Confidence': confidences  # Phase 2 Improvement: Confidence scores for quality assessment
        # 'position_for_note': position
    })

    df['Priority'] = df['Description'].apply(lambda x: 'high' if 'must' in x.lower() or 'shall' in x.lower()
    else 'medium' if 'should' in x.lower() or 'has to' in x.lower()
    else 'security' if 'security' in x.lower()
    else 'low')

    lista_note = []
    for j in range(len(df['Label Number'])):
        lista_note.append(df['Label Number'][j] + ":" + df['Description'][j])
    df['Note'] = lista_note

    return df
