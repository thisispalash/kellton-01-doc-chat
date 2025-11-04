"""PDF processing and embedding generation."""

import re
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from ..config import Config

# Global embedding model - loaded once
_embedding_model = None


def get_embedding_model():
    """Get or initialize the embedding model.
    
    Returns:
        SentenceTransformer model
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
    return _embedding_model


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        List of tuples (page_number, text) for each page
    """
    try:
        reader = PdfReader(file_path)
        pages = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():  # Only include non-empty pages
                pages.append((i + 1, text))
        
        return pages
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []


def clean_text(text):
    """Clean and normalize text.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.,!?;:\-\(\)]', '', text)
    return text.strip()


def chunk_text(text, chunk_size=None, overlap=None):
    """Chunk text into smaller pieces with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters (default from config)
        overlap: Overlap between chunks in characters (default from config)
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = Config.CHUNK_SIZE
    if overlap is None:
        overlap = Config.CHUNK_OVERLAP
    
    # Clean the text first
    text = clean_text(text)
    
    # Split into words for better chunking
    words = text.split()
    chunks = []
    
    # Estimate characters per word (average ~5)
    words_per_chunk = chunk_size // 5
    words_overlap = overlap // 5
    
    for i in range(0, len(words), words_per_chunk - words_overlap):
        chunk_words = words[i:i + words_per_chunk]
        if chunk_words:
            chunks.append(' '.join(chunk_words))
        
        # Break if we've processed all words
        if i + words_per_chunk >= len(words):
            break
    
    return chunks


def process_pdf_to_chunks(file_path):
    """Process a PDF file into text chunks with metadata.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        List of dicts with 'text', 'page_number', and 'chunk_index'
    """
    pages = extract_text_from_pdf(file_path)
    all_chunks = []
    chunk_index = 0
    
    for page_number, page_text in pages:
        chunks = chunk_text(page_text)
        
        for chunk in chunks:
            all_chunks.append({
                'text': chunk,
                'page_number': page_number,
                'chunk_index': chunk_index
            })
            chunk_index += 1
    
    return all_chunks


def generate_embeddings(texts):
    """Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings
        
    Returns:
        List of embedding vectors
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def generate_embedding(text):
    """Generate embedding for a single text.
    
    Args:
        text: Text string
        
    Returns:
        Embedding vector as list
    """
    return generate_embeddings([text])[0]

