"""
pdf_digestible.py
==================

This script is designed to make large PDF documents easier to consume in
contexts such as language model processing.  It downloads a PDF from a
URL (or reads from a local path), converts it to plain text using the
`pdftotext` command-line utility, splits the document into pages and
summarises each page using a simple frequency‑based extractive
summarisation algorithm.  The result is a lightweight representation
that preserves the most important sentences from each page while
reducing the overall length of the text.

The summarisation function relies solely on Python's standard library
and avoids external dependencies that may not be available in all
environments.  A basic list of English stopwords is embedded to
improve sentence scoring.  Adjust the `SUMMARY_RATIO` constant to
increase or decrease the proportion of sentences retained from each
page (for example, 0.3 retains roughly the top 30 % of sentences by
score).

Usage:

    python pdf_digestible.py --url <PDF_URL> [--output summary.json] [--ratio 0.3]

If no URL is provided, the script can also process a local file by
specifying `--file <PATH_TO_PDF>`.  The output is written to a JSON
file containing an array of objects with page numbers and their
summaries.
"""

import argparse
import json
import os
import re
import string
import subprocess
import sys
import tempfile
from typing import List, Tuple

try:
    # urllib is part of the standard library
    from urllib import request as urllib_request
except ImportError:
    import urllib.request as urllib_request  # type: ignore

# A simple set of English stopwords.  This list is adapted from the
# NLTK corpus and includes common function words, contractions and
# negations.  It is intentionally limited to reduce the likelihood of
# discarding domain‑specific terms found in financial reports.
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an',
    'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been',
    'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can',
    "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does',
    "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have',
    "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here',
    "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how',
    "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is',
    "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most',
    "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on',
    'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves',
    'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll",
    "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that',
    "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then',
    'there', "there's", 'these', 'they', "they'd", "they'll", "they're",
    "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until',
    'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're",
    "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where',
    "where's", 'which', 'while', 'who', "who's", 'whom', 'why',
    "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll",
    "you're", "you've", 'your', 'yours', 'yourself', 'yourselves'
}


def download_pdf(url: str, dest_path: str) -> str:
    """Download a PDF from a URL to a destination path.

    Args:
        url: The URL of the PDF to download.
        dest_path: The file path where the PDF should be saved.

    Returns:
        The path to the downloaded file.

    Raises:
        URLError: If the download fails.
    """
    # Use urllib to download the file in chunks
    with urllib_request.urlopen(url) as response, open(dest_path, 'wb') as out_file:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out_file.write(chunk)
    return dest_path


def pdf_to_text(pdf_path: str) -> str:
    """Convert a PDF file to plain text using the pdftotext command.

    This function requires that the `pdftotext` utility from the
    poppler suite is installed and available in the system PATH.  If
    conversion fails, a RuntimeError will be raised.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A string containing the text extracted from the PDF.
    """
    # Create a temporary file to hold the text output
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
        txt_path = tmp.name
    try:
        # Use -layout to preserve the relative positions of text.  If the
        # layout option causes issues, consider removing it.
        result = subprocess.run(
            ['pdftotext', '-layout', pdf_path, txt_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"pdftotext failed with code {result.returncode}: {result.stderr.decode('utf-8', errors='ignore')}"
            )
        # Read the generated text
        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    finally:
        # Ensure the temporary text file is removed
        try:
            os.remove(txt_path)
        except OSError:
            pass
    return text


def split_into_sentences(text: str) -> List[str]:
    """Simple sentence splitter based on punctuation and newlines.

    Args:
        text: A block of text.

    Returns:
        A list of sentence strings.
    """
    # Normalise whitespace and remove repeated newlines
    cleaned = re.sub(r'[\n\r]+', ' ', text)
    # Insert a marker after sentence‑ending punctuation followed by space
    sentence_endings = re.compile(r'([.!?])\s+')
    parts = sentence_endings.split(cleaned)
    sentences: List[str] = []
    buffer = ''
    for i in range(0, len(parts), 2):
        segment = parts[i]
        if i + 1 < len(parts):
            punctuation = parts[i + 1]
        else:
            punctuation = ''
        buffer += segment + punctuation
        if punctuation:
            # End of sentence
            sent = buffer.strip()
            if sent:
                sentences.append(sent)
            buffer = ''
    # Append any residual buffer as a sentence
    residual = buffer.strip()
    if residual:
        sentences.append(residual)
    return sentences


def tokenize(text: str) -> List[str]:
    """Tokenise a string into lower‑case words, removing punctuation.

    Args:
        text: The input string.

    Returns:
        A list of tokens (words).
    """
    # Remove punctuation and split on whitespace
    translator = str.maketrans('', '', string.punctuation)
    stripped = text.translate(translator)
    tokens = [word.lower() for word in stripped.split() if word]
    return tokens


def build_frequency_table(text: str) -> dict:
    """Build a frequency table of words for a given text.

    Stopwords are excluded and only words with at least two characters
    are considered to reduce noise.

    Args:
        text: The input string to analyse.

    Returns:
        A dictionary mapping words to their frequency counts.
    """
    freq_table: dict = {}
    tokens = tokenize(text)
    for word in tokens:
        if word in STOPWORDS or len(word) < 2:
            continue
        freq_table[word] = freq_table.get(word, 0) + 1
    return freq_table


def score_sentences(sentences: List[str], freq_table: dict) -> dict:
    """Score sentences based on the frequencies of their constituent words.

    Args:
        sentences: A list of sentences to score.
        freq_table: A dictionary of word frequencies.

    Returns:
        A dictionary mapping sentences to their computed scores.
    """
    scores: dict = {}
    for sentence in sentences:
        sentence_tokens = tokenize(sentence)
        if not sentence_tokens:
            continue
        # Sum frequencies of all words present in this sentence
        score = 0
        for word in sentence_tokens:
            if word in freq_table:
                score += freq_table[word]
        # Normalise by number of significant words to avoid bias
        if score > 0:
            scores[sentence] = score / len(sentence_tokens)
    return scores


def summarise(text: str, ratio: float = 0.3) -> str:
    """Summarise a block of text using an extractive method.

    This function selects the highest scoring sentences based on word
    frequencies.  The `ratio` parameter determines what fraction of
    sentences will be retained.  The selected sentences are returned
    in their original order to preserve context.

    Args:
        text: The input text to summarise.
        ratio: Fraction of sentences to retain (between 0 and 1).

    Returns:
        A summary string composed of the selected sentences.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return ''
    # Build frequency table from the whole text to capture global context
    freq_table = build_frequency_table(text)
    scores = score_sentences(sentences, freq_table)
    # Determine how many sentences to select
    n_sentences = max(1, int(len(sentences) * ratio))
    # Sort sentences by score (descending) and take top n
    # Use enumerate to tie sentence to its index for order restoration
    scored_sentences: List[Tuple[int, str, float]] = []
    for idx, sentence in enumerate(sentences):
        score = scores.get(sentence, 0)
        scored_sentences.append((idx, sentence, score))
    # Select top n based on score
    scored_sentences.sort(key=lambda tup: tup[2], reverse=True)
    selected = scored_sentences[:n_sentences]
    # Sort selected sentences back to their original order
    selected.sort(key=lambda tup: tup[0])
    summary_sentences = [sentence for _, sentence, _ in selected]
    summary = ' '.join(summary_sentences)
    return summary


def process_pdf(pdf_source: str, summary_ratio: float = 0.3) -> List[dict]:
    """Process a PDF file and produce a summary for each page.

    Args:
        pdf_source: Path to the PDF file.
        summary_ratio: Ratio of sentences to keep in each page summary.

    Returns:
        A list of dictionaries with keys ``page`` and ``summary``.
    """
    full_text = pdf_to_text(pdf_source)
    # Split on form feed characters to separate pages
    pages = full_text.split('\f')
    summaries: List[dict] = []
    for i, page_text in enumerate(pages, start=1):
        # Trim whitespace and skip empty pages
        cleaned = page_text.strip()
        if not cleaned:
            continue
        summary = summarise(cleaned, ratio=summary_ratio)
        summaries.append({'page': i, 'summary': summary})
    return summaries


def main():
    parser = argparse.ArgumentParser(
        description='Extract and summarise text from a PDF to make it more digestible.',
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', type=str, help='URL of the PDF to process')
    group.add_argument('--file', type=str, help='Path to a local PDF file to process')
    parser.add_argument('--output', type=str, default='summary.json', help='Output JSON file')
    parser.add_argument('--ratio', type=float, default=0.3, help='Summary ratio per page (0 < ratio ≤ 1)')
    args = parser.parse_args()
    # Validate ratio
    if not (0 < args.ratio <= 1):
        parser.error('The --ratio value must be between 0 (exclusive) and 1 (inclusive).')
    # Download if URL is provided
    if args.url:
        # Determine filename from URL
        filename = os.path.basename(args.url.split('?')[0]) or 'downloaded.pdf'
        temp_pdf_path = os.path.join(tempfile.gettempdir(), filename)
        print(f'Downloading PDF from {args.url}...')
        pdf_path = download_pdf(args.url, temp_pdf_path)
    else:
        pdf_path = args.file
        if not os.path.isfile(pdf_path):
            print(f'File not found: {pdf_path}', file=sys.stderr)
            sys.exit(1)
    # Process the PDF
    print('Processing PDF...')
    summaries = process_pdf(pdf_path, summary_ratio=args.ratio)
    # Write summaries to JSON
    with open(args.output, 'w', encoding='utf-8') as out_f:
        json.dump(summaries, out_f, indent=2, ensure_ascii=False)
    print(f'Generated summary for {len(summaries)} pages and saved to {args.output}')


if __name__ == '__main__':
    main()
