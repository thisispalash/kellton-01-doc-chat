"""File storage management for uploaded documents."""

import os
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename
from ..config import Config


def allowed_file(filename):
    """Check if a file has an allowed extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def get_user_upload_dir(user_id):
    """Get the upload directory for a specific user.
    
    Args:
        user_id: User ID
        
    Returns:
        Path object for user's upload directory
    """
    user_dir = Path(Config.UPLOADS_PATH) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def save_file(file, user_id, document_id):
    """Save an uploaded file to disk.
    
    Args:
        file: FileStorage object from Flask request
        user_id: User ID
        document_id: Document ID for naming
        
    Returns:
        Tuple of (file_path, filename) if successful, (None, None) otherwise
    """
    if not file or not allowed_file(file.filename):
        return None, None
    
    # Secure the filename
    original_filename = secure_filename(file.filename)
    
    # Create filename with document ID
    ext = original_filename.rsplit('.', 1)[1].lower()
    new_filename = f"{document_id}.{ext}"
    
    # Get user directory
    user_dir = get_user_upload_dir(user_id)
    file_path = user_dir / new_filename
    
    # Save file
    try:
        file.save(str(file_path))
        return str(file_path), original_filename
    except Exception as e:
        print(f"Error saving file: {e}")
        return None, None


def get_file_path(user_id, document_id, extension='pdf'):
    """Get the file path for a document.
    
    Args:
        user_id: User ID
        document_id: Document ID
        extension: File extension (default: pdf)
        
    Returns:
        Path object for the file
    """
    user_dir = Path(Config.UPLOADS_PATH) / str(user_id)
    return user_dir / f"{document_id}.{extension}"


def delete_file(file_path):
    """Delete a file from disk.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if file was deleted, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def delete_user_files(user_id):
    """Delete all files for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        True if directory was deleted, False otherwise
    """
    try:
        user_dir = Path(Config.UPLOADS_PATH) / str(user_id)
        if user_dir.exists():
            shutil.rmtree(user_dir)
            return True
        return False
    except Exception as e:
        print(f"Error deleting user files: {e}")
        return False


def get_file_size(file_path):
    """Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size
        return 0
    except Exception as e:
        print(f"Error getting file size: {e}")
        return 0

