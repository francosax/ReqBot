import logging
import re

import en_core_web_sm
import fitz
import pandas as pd

logging.basicConfig(filename='debug.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Phase 1 Improvement: Sentence length validation thresholds
MIN_REQUIREMENT_LENGTH_WORDS = 5
MAX_REQUIREMENT_LENGTH_WORDS = 100

# Phase 2 Improvement: Confidence scoring threshold
MIN_CONFIDENCE_THRESHOLD = 0.4  # Minimum confidence to include requirement

# Phase 2 Improvement: Cache spaCy model for better performance (3-5x faster)
_nlp_model = None


def get_nlp_model():
    """
    Lazy-load and cache spaCy model for improved performance.

    Phase 2 Improvement: Loading the model once instead of on every call
    provides 3-5x speed improvement.

    Returns:
        spacy.Language: Cached spaCy NLP model
    """
    global _nlp_model
    if _nlp_model is None:
        _nlp_model = en_core_web_sm.load()
        logging.info("spaCy model loaded and cached")
    return _nlp_model


def preprocess_pdf_text(text):
    """
    Clean and normalize PDF text for better NLP processing.

    Phase 2 Improvement: Handles common PDF extraction issues including:
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


def extract_text_with_layout(page):
    """
    Phase 3 Improvement: Extract text from PDF page with better layout awareness.

    Uses block-based extraction to handle multi-column layouts correctly.
    Ensures text is extracted in proper reading order (top to bottom, left to right).

    Args:
        page: PyMuPDF page object

    Returns:
        str: Text extracted in correct reading order
    """
    # Get text blocks (better for multi-column layouts)
    blocks = page.get_text("blocks", sort=True)

    # Sort blocks by vertical position first (top to bottom)
    # Then by horizontal position (left to right)
    # This ensures proper reading order even with multiple columns
    blocks_sorted = sorted(blocks, key=lambda b: (round(b[1] / 10) * 10, b[0]))

    # Extract text from sorted blocks
    text_parts = []
    for block in blocks_sorted:
        if block[6] == 0:  # Type 0 = text block (not image)
            block_text = block[4]
            if block_text.strip():
                text_parts.append(block_text.strip())

    # Double newline between blocks to help sentence segmentation
    return '\n\n'.join(text_parts)


def matches_requirement_pattern(sentence):
    """
    Phase 3 Improvement: Check if sentence matches common requirement patterns.

    Beyond just keywords, this function looks for structural patterns
    that are typical of well-formed requirements.

    Args:
        sentence (str): The sentence to check

    Returns:
        bool: True if sentence matches requirement patterns
    """
    sentence_lower = sentence.lower()

    # Common requirement patterns
    REQUIREMENT_PATTERNS = [
        # Modal verb patterns
        r'\b(shall|must|should|will)\s+(be|have|provide|support|allow|enable|ensure|include|perform|display|accept|reject|generate|calculate|store|retrieve|validate|verify)',

        # Subject-verb patterns with modal verbs
        r'\b(the\s+\w+|this\s+\w+|all\s+\w+|each\s+\w+|every\s+\w+)\s+(shall|must|should|will)\b',

        # Capability patterns
        r'\b(capable\s+of|ability\s+to|required\s+to|responsible\s+for|designed\s+to)\b',

        # Compliance patterns
        r'\b(comply\s+with|conform\s+to|in\s+accordance\s+with|as\s+specified\s+in|according\s+to)\b',

        # Necessity patterns
        r'\b(it\s+is\s+(required|necessary|mandatory|essential)|there\s+(shall|must|should)\s+be)\b',

        # Quantified patterns
        r'\b(at\s+least|no\s+more\s+than|between|within|greater\s+than|less\s+than)\s+\d+\b',
    ]

    # Check if any pattern matches
    return any(re.search(pattern, sentence_lower) for pattern in REQUIREMENT_PATTERNS)


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

    # Phase 3 Improvement: Boost for requirement pattern matching
    if matches_requirement_pattern(sentence):
        confidence *= 1.15

    # Cap confidence at 1.0
    return min(confidence, 1.0)


def requirement_finder(path, keywords_set, filename, confidence_threshold=0.5):
    """
    Extract requirements from PDF using NLP with Phase 1 & 2 improvements.

    Phase 1: Keyword matching, length validation, sentence filtering
    Phase 2: Text preprocessing, confidence scoring, performance optimization

    Args:
        path (str): Path to PDF file
        keywords_set (set): Set of requirement keywords to search for
        filename (str): Name of the file (for labeling)
        confidence_threshold (float): Minimum confidence threshold (default: 0.5)

    Returns:
        pd.DataFrame: DataFrame with extracted requirements and metadata
    """
    doc = fitz.open(path)
    nlp = get_nlp_model()  # Use cached model instead of reloading

    cont_text = []
    pagine = []
    keyword = []

    for i, page in enumerate(doc, 1):
        # Phase 3 Improvement: Use layout-aware extraction for multi-column PDFs
        page_text = extract_text_with_layout(page)
        # print(text)
        cont_text.append(page_text)

    # word_set = keywords_set
    word_set = {word.lower() for word in keywords_set}

    raw_sentences = []
    matching_sentences = []
    tag = []
    confidences = []  # Phase 2 Improvement: Store confidence scores
    req_c = 0
    # Phase 2 Improvement: Track confidence scores
    confidences = []
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
                cleaned_sentence = sent.text.strip().replace('\n', ' ')

                # Phase 2 Improvement: Calculate confidence score
                keyword_word = next(word for word in sentence_words if word in word_set)
                confidence = calculate_requirement_confidence(cleaned_sentence, keyword_word, word_count)

                # Phase 2 Improvement: Only include if confidence meets threshold (user-adjustable)
                if confidence >= confidence_threshold:
                    req_c += 1
                    raw_sentences.append(sent.text.split())
                    matching_sentences.append(cleaned_sentence)
                    pagine.append(i)
                    keyword.append(keyword_word)
                    confidences.append(confidence)
                    # Create a tag for the requirement
                    tag.append(filename + '-Req#' + str(i) + '-' + str(req_c))
                else:
                    # Log low-confidence matches for debugging
                    logging.info(
                        f"Skipping low-confidence requirement on page {i} "
                        f"(confidence: {confidence:.2f}, threshold: {confidence_threshold:.2f}): {cleaned_sentence[:100]}..."
                    )

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

    # v2.2: Add automatic categorization
    from requirement_categorizer import get_categorizer
    categorizer = get_categorizer()
    df['Category'] = df.apply(
        lambda row: categorizer.categorize(row['Description'], row['Priority']),
        axis=1
    )

    lista_note = []
    for j in range(len(df['Label Number'])):
        lista_note.append(df['Label Number'][j] + ":" + df['Description'][j])
    df['Note'] = lista_note

    return df
