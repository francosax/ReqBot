"""
Multi-lingual PDF Requirement Analyzer

Enhanced version of pdf_analyzer.py with multi-lingual support.
Automatically detects document language and uses appropriate NLP models.

Version History:
- v1.0: Original English-only version
- v2.0: Added preprocessing and confidence scoring
- v2.1: Added layout-aware extraction and pattern matching
- v2.2: Added automatic categorization
- v3.0: Added multi-lingual support (en, fr, de, it, es)

Author: ReqBot Development Team
Version: 3.0.0
Date: 2025-11-18
"""

import logging
import re
from typing import Set, Optional

import fitz
import pandas as pd

# Multi-lingual support imports (v3.0)
from language_detector import detect_language
from language_config import get_language_config
from multilingual_nlp import get_nlp

logging.basicConfig(filename='debug.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Phase 1 Improvement: Sentence length validation thresholds
MIN_REQUIREMENT_LENGTH_WORDS = 5
MAX_REQUIREMENT_LENGTH_WORDS = 100

# Phase 2 Improvement: Confidence scoring threshold
MIN_CONFIDENCE_THRESHOLD = 0.4  # Minimum confidence to include requirement


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


def detect_document_language(doc, sample_pages=3) -> tuple:
    """
    v3.0: Detect the primary language of a PDF document.

    Samples text from first few pages to determine language.

    Args:
        doc: PyMuPDF document object
        sample_pages: Number of pages to sample (default: 3)

    Returns:
        tuple: (language_code, confidence_score)
    """
    # Collect text from first N pages
    sample_text = []
    for page_num in range(min(sample_pages, len(doc))):
        page = doc[page_num]
        page_text = extract_text_with_layout(page)
        sample_text.append(page_text)

    combined_text = '\n'.join(sample_text)

    # Detect language
    lang_code, confidence = detect_language(combined_text)

    logger = logging.getLogger(__name__)
    logger.info(f"Detected document language: {lang_code} (confidence: {confidence:.2%})")

    return (lang_code, confidence)


def get_requirement_patterns(lang_code: str) -> list:
    """
    v3.0: Get language-specific requirement patterns.

    Returns regex patterns for identifying requirements in different languages.

    Args:
        lang_code: ISO 639-1 language code

    Returns:
        list: List of regex patterns for the language
    """
    patterns = {
        'en': [
            # Modal verb patterns
            r'\b(shall|must|should|will)\s+(be|have|provide|support|allow|enable|ensure|include|perform|display|accept|reject|generate|calculate|store|retrieve|validate|verify)',  # noqa: E501
            # Subject-verb patterns
            r'\b(the\s+\w+|this\s+\w+|all\s+\w+|each\s+\w+|every\s+\w+)\s+(shall|must|should|will)\b',
            # Capability patterns
            r'\b(capable\s+of|ability\s+to|required\s+to|responsible\s+for|designed\s+to)\b',
            # Compliance patterns
            r'\b(comply\s+with|conform\s+to|in\s+accordance\s+with|as\s+specified\s+in|according\s+to)\b',
            # Necessity patterns
            r'\b(it\s+is\s+(required|necessary|mandatory|essential)|there\s+(shall|must|should)\s+be)\b',
        ],
        'fr': [
            # Modal patterns (French)
            r'\b(doit|devra|devrait|peut)\s+(être|avoir|fournir|supporter|permettre|assurer|inclure|effectuer)\b',
            # Subject-verb patterns
            r'\b(le\s+\w+|la\s+\w+|les\s+\w+|ce\s+\w+|chaque\s+\w+)\s+(doit|devra|devrait)\b',
            # Capability patterns
            r'\b(capable\s+de|capacité\s+de|obligatoire\s+de|responsable\s+de|conçu\s+pour)\b',
            # Compliance patterns
            r'\b(conformément\s+à|conforme\s+à|selon|en\s+accord\s+avec)\b',
        ],
        'de': [
            # Modal patterns (German)
            r'\b(muss|soll|sollte|kann)\s+(sein|haben|bereitstellen|unterstützen|ermöglichen|gewährleisten|beinhalten)\b',
            # Subject-verb patterns
            r'\b(das\s+\w+|die\s+\w+|der\s+\w+|jede[rs]?\s+\w+)\s+(muss|soll|sollte)\b',
            # Capability patterns
            r'\b(fähig\s+zu|in\s+der\s+Lage\s+zu|erforderlich\s+zu|verantwortlich\s+für)\b',
            # Compliance patterns
            r'\b(entsprechend|gemäß|in\s+Übereinstimmung\s+mit|laut)\b',
        ],
        'it': [
            # Modal patterns (Italian)
            r'\b(deve|dovrà|dovrebbe|può)\s+(essere|avere|fornire|supportare|permettere|garantire|includere)\b',
            # Subject-verb patterns
            r'\b(il\s+\w+|la\s+\w+|i\s+\w+|le\s+\w+|ogni\s+\w+)\s+(deve|dovrà|dovrebbe)\b',
            # Capability patterns
            r'\b(capace\s+di|capacità\s+di|obbligatorio|responsabile\s+di|progettato\s+per)\b',
            # Compliance patterns
            r'\b(conforme\s+a|in\s+conformità\s+con|secondo|come\s+specificato\s+in)\b',
        ],
        'es': [
            # Modal patterns (Spanish)
            r'\b(debe|deberá|debería|puede)\s+(ser|tener|proporcionar|soportar|permitir|asegurar|incluir)\b',
            # Subject-verb patterns
            r'\b(el\s+\w+|la\s+\w+|los\s+\w+|las\s+\w+|cada\s+\w+)\s+(debe|deberá|debería)\b',
            # Capability patterns
            r'\b(capaz\s+de|capacidad\s+de|obligatorio|responsable\s+de|diseñado\s+para)\b',
            # Compliance patterns
            r'\b(conforme\s+a|de\s+acuerdo\s+con|según|como\s+se\s+especifica\s+en)\b',
        ]
    }

    return patterns.get(lang_code, patterns['en'])


def matches_requirement_pattern(sentence: str, lang_code: str = 'en') -> bool:
    """
    v3.0: Check if sentence matches requirement patterns for specific language.

    Args:
        sentence: The sentence to check
        lang_code: Language code for pattern selection

    Returns:
        bool: True if sentence matches requirement patterns
    """
    sentence_lower = sentence.lower()
    patterns = get_requirement_patterns(lang_code)

    # Check if any pattern matches
    return any(re.search(pattern, sentence_lower) for pattern in patterns)


def calculate_requirement_confidence(
    sentence: str,
    keyword: str,
    word_count: int,
    lang_code: str = 'en'
) -> float:
    """
    v3.0: Calculate confidence score for a potential requirement (multi-lingual).

    Uses multiple factors to assess requirement quality:
    - Sentence length (optimal: 8-50 words)
    - Presence of multiple requirement keywords
    - Language-specific requirement patterns
    - Header detection (penalized)
    - High number density (penalized)

    Args:
        sentence: The extracted sentence text
        keyword: The keyword that triggered the match
        word_count: Number of words in the sentence
        lang_code: Language code for language-specific checks

    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    confidence = 1.0
    sentence_lower = sentence.lower()

    # Factor 1: Sentence length
    if word_count < 5:
        confidence *= 0.3
    elif word_count < 8:
        confidence *= 0.7
    elif 8 <= word_count <= 50:
        confidence *= 1.0
    elif 50 < word_count <= 80:
        confidence *= 0.8
    else:
        confidence *= 0.5

    # Factor 2: Multiple requirement keywords (language-specific)
    config = get_language_config()
    requirement_keywords = config.get_keywords(lang_code)
    keyword_count = sum(1 for kw in requirement_keywords if kw in sentence_lower)

    if keyword_count >= 2:
        confidence *= 1.2
    elif keyword_count >= 3:
        confidence *= 1.3

    # Factor 3: Language-specific requirement patterns
    if matches_requirement_pattern(sentence, lang_code):
        confidence *= 1.15

    # Factor 4: Penalize headers
    if sentence.isupper() and word_count <= 6:
        confidence *= 0.4
    elif word_count <= 3:
        confidence *= 0.5

    # Factor 5: Penalize table data (lots of numbers)
    numbers = re.findall(r'\d+', sentence)
    if len(numbers) > word_count * 0.3:
        confidence *= 0.6

    # Factor 6: Boost for compliance indicators (language-aware)
    compliance_terms = {
        'en': ['comply with', 'conform to', 'capable of', 'ability to'],
        'fr': ['conforme à', 'conformément à', 'capable de'],
        'de': ['entsprechend', 'gemäß', 'fähig zu'],
        'it': ['conforme a', 'capace di'],
        'es': ['conforme a', 'capaz de']
    }

    lang_terms = compliance_terms.get(lang_code, compliance_terms['en'])
    if any(term in sentence_lower for term in lang_terms):
        confidence *= 1.1

    # Cap at 1.0
    return min(confidence, 1.0)


def determine_priority(sentence: str, lang_code: str = 'en') -> str:
    """
    v3.0: Determine requirement priority based on keywords (multi-lingual).

    Args:
        sentence: Requirement text
        lang_code: Language code for priority keywords

    Returns:
        str: Priority level ('high', 'medium', 'low', 'security')
    """
    sentence_lower = sentence.lower()
    config = get_language_config()

    # Check for security keywords first (highest priority)
    security_keywords = config.get_security_keywords(lang_code)
    if any(kw in sentence_lower for kw in security_keywords):
        return 'security'

    # Check high-priority keywords
    high_keywords = config.get_priority_keywords(lang_code, 'high')
    if any(kw in sentence_lower for kw in high_keywords):
        return 'high'

    # Check medium-priority keywords
    medium_keywords = config.get_priority_keywords(lang_code, 'medium')
    if any(kw in sentence_lower for kw in medium_keywords):
        return 'medium'

    # Default to low priority
    return 'low'


def requirement_finder(
    path: str,
    keywords_set: Set[str],
    filename: str,
    confidence_threshold: float = 0.5,
    auto_detect_language: bool = True,
    force_language: Optional[str] = None
) -> pd.DataFrame:
    """
    v3.0: Extract requirements from PDF with multi-lingual support.

    New in v3.0:
    - Automatic language detection
    - Multi-lingual NLP processing
    - Language-specific patterns and keywords
    - Graceful fallback to English

    Args:
        path: Path to PDF file
        keywords_set: Set of requirement keywords (used if force_language set)
        filename: Name of the file (for labeling)
        confidence_threshold: Minimum confidence threshold (default: 0.5)
        auto_detect_language: Automatically detect document language (default: True)
        force_language: Force specific language (overrides auto-detection)

    Returns:
        pd.DataFrame: DataFrame with extracted requirements and metadata
    """
    logger = logging.getLogger(__name__)
    doc = fitz.open(path)
    nlp_manager = get_nlp()
    config = get_language_config()

    # Step 1: Determine document language
    if force_language:
        lang_code = force_language
        lang_confidence = 1.0
        logger.info(f"Using forced language: {lang_code}")
    elif auto_detect_language:
        lang_code, lang_confidence = detect_document_language(doc)
        logger.info(f"Auto-detected language: {lang_code} ({lang_confidence:.2%})")
    else:
        lang_code = 'en'
        lang_confidence = 1.0
        logger.info("Using default language: English")

    # Step 2: Get language-specific keywords
    if auto_detect_language or force_language:
        keywords_set = config.get_keywords(lang_code)
        logger.info(f"Using {len(keywords_set)} keywords for {lang_code}")

    # Step 3: Extract text from all pages
    cont_text = []
    for i, page in enumerate(doc, 1):
        page_text = extract_text_with_layout(page)
        cont_text.append(page_text)

    # Normalize keywords to lowercase
    word_set = {word.lower() for word in keywords_set}

    # Initialize result containers
    raw_sentences = []
    matching_sentences = []
    tag = []
    pages = []
    keywords = []
    confidences = []
    req_c = 0
    current_page = None

    # Step 4: Process each page
    for i, page_text in enumerate(cont_text, 1):
        if i != current_page:
            req_c = 0
            current_page = i

        # Use multilingual NLP for sentence extraction
        sentences = nlp_manager.extract_sentences(
            page_text,
            lang_code=lang_code,
            min_words=MIN_REQUIREMENT_LENGTH_WORDS,
            max_words=MAX_REQUIREMENT_LENGTH_WORDS
        )

        for sent in sentences:
            # Check if sentence contains requirement keywords
            sentence_words = set(word.lower() for word in sent.tokens)
            matched_keywords = sentence_words & word_set

            if matched_keywords:
                keyword_word = list(matched_keywords)[0]

                # Calculate confidence
                confidence = calculate_requirement_confidence(
                    sent.text,
                    keyword_word,
                    sent.word_count,
                    lang_code
                )

                # Apply confidence threshold
                if confidence >= confidence_threshold:
                    req_c += 1
                    raw_sentences.append(sent.tokens)
                    matching_sentences.append(sent.text)
                    pages.append(i)
                    keywords.append(keyword_word)
                    confidences.append(confidence)
                    tag.append(f"{filename}-Req#{i}-{req_c}")
                else:
                    logger.info(
                        f"Skipping low-confidence requirement on page {i} "
                        f"(confidence: {confidence:.2f}): {sent.text[:100]}..."
                    )

    # Step 5: Create DataFrame
    df = pd.DataFrame({
        'Label Number': tag,
        'Description': matching_sentences,
        'Page': pages,
        'Keyword': keywords,
        'Raw': raw_sentences,
        'Confidence': confidences,
        'Language': [lang_code] * len(tag)  # v3.0: Track document language
    })

    # Step 6: Assign priorities (language-aware)
    df['Priority'] = df['Description'].apply(lambda x: determine_priority(x, lang_code))

    # Step 7: Automatic categorization
    try:
        from requirement_categorizer import get_categorizer
        categorizer = get_categorizer()
        df['Category'] = df.apply(
            lambda row: categorizer.categorize(row['Description'], row['Priority']),
            axis=1
        )
    except ImportError:
        logger.warning("requirement_categorizer not available, skipping categorization")
        df['Category'] = 'Uncategorized'

    # Step 8: Create note field
    df['Note'] = df.apply(lambda row: f"{row['Label Number']}:{row['Description']}", axis=1)

    logger.info(f"Extracted {len(df)} requirements from {filename} ({lang_code})")

    return df


# Backward compatibility: Keep old function signature
def requirement_finder_v2(path, keywords_set, filename, confidence_threshold=0.5):
    """
    Legacy function for backward compatibility.
    Calls the new multilingual version with auto-detection disabled.
    """
    return requirement_finder(
        path,
        keywords_set,
        filename,
        confidence_threshold,
        auto_detect_language=False,
        force_language='en'
    )
