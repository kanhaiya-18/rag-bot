import cloudinary.uploader
import io
from utils.cloudinary_config import cloudinary_config

cloudinary_config()

def upload_in_cloudinary(pdf_bytes, filename="document.pdf"):
    clean_name = filename if filename else "document.pdf"
    if not clean_name.lower().endswith(".pdf"):
        clean_name = f"{clean_name}.pdf"

    return cloudinary.uploader.upload(
        io.BytesIO(pdf_bytes),
        resource_type="raw", 
        folder="my_pdfs",
        public_id=clean_name,
        use_filename=True,
        unique_filename=True
    )