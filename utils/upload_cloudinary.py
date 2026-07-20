import cloudinary.uploader
import io
def upload_in_cloudinary(pdf_bytes):
    return cloudinary.uploader.upload(
        io.BytesIO(pdf_bytes),
        resource_type="raw", 
        folder="my_pdfs",
        use_filename=True,
        unique_filename=True
        )