import os
import logging
from src.config import settings

logger = logging.getLogger("jobexa.services.storage")

class StorageService:
    @staticmethod
    def upload_file(file_bytes: bytes, filename: str, folder: str = "documents") -> str:
        """
        Uploads a file to cloud storage (Supabase) or falls back to local static directory.
        Returns the public URL of the uploaded file.
        """
        # Validate file size (max 5MB per file - Principle IX)
        MAX_SIZE = 5 * 1024 * 1024
        if len(file_bytes) > MAX_SIZE:
            raise ValueError("File size exceeds the maximum limit of 5MB.")

        # If Supabase URL and Key are available, attempt upload
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                
                # Unique remote path
                import uuid
                unique_filename = f"{uuid.uuid4()}_{filename}"
                storage_path = f"{folder}/{unique_filename}"
                
                # Upload to bucket
                response = supabase_client.storage.from_(settings.SUPABASE_BUCKET).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": "application/pdf"}
                )
                
                # Get public url
                public_url = supabase_client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(storage_path)
                logger.info(f"Uploaded file to Supabase Storage: {public_url}")
                return public_url
            except Exception as e:
                logger.error(f"Supabase upload failed: {str(e)}. Falling back to local storage.")

        # Local static directory fallback
        logger.info("Using local static storage fallback.")
        # Local upload directory: backend/static/uploads
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "uploads"))
        os.makedirs(static_dir, exist_ok=True)
        
        import uuid
        unique_filename = f"{uuid.uuid4()}_{filename}"
        local_path = os.path.join(static_dir, unique_filename)
        
        try:
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            # Yield localhost url representation
            local_url = f"http://localhost:8000/static/uploads/{unique_filename}"
            logger.info(f"Local file saved: {local_url}")
            return local_url
        except Exception as local_err:
            logger.error(f"Local file save failed: {str(local_err)}")
            raise local_err
