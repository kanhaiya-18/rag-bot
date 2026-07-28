import io
import zipfile
import urllib.request
import cloudinary.utils
from utils.cloudinary_config import cloudinary_config
from fastapi import UploadFile, File, HTTPException, status, BackgroundTasks, Response
from db.database import documets, user_collection
from utils.vector_store import extract_text, split_text
from utils.upload_cloudinary import upload_in_cloudinary
from helpers.delete_from_qdrant import delete_qdrant_chunks
import cloudinary.uploader
from bson import ObjectId
cloudinary_config()

async def process_pdf_in_background(doc_id: ObjectId, pdf_bytes: bytes, filename: str, public_id: str, user: dict):
    """
    Background worker: Extracts text, creates embeddings in Qdrant,
    and updates MongoDB status to 'ready' (or 'failed' on error).
    """
    try:
        # 1. Extract text from PDF
        text = extract_text(pdf_bytes)
        
        # 2. Chunk text & store vectors in Qdrant
        split_text(text, filename, str(doc_id), public_id, user)
        
        # 3. Update status in MongoDB to 'ready'
        await documets.update_one(
            {"_id": doc_id},
            {"$set": {"status": "ready"}}
        )
        print(f"PDF background processing complete: {doc_id}")
    except Exception as e:
        print(f"Background processing error: {e}")
        # Mark document as failed so user knows processing failed
        await documets.update_one(
            {"_id": doc_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )



async def upload_file(background_task: BackgroundTasks,user ,file: UploadFile = File(...)):
    # print(user)
    user_exist = await user_collection.find_one({"email" : user["email"]})
    if not user_exist :
        raise HTTPException(400,detail="user doesnt exist")
    # print("1.user verified")
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="file type should be pdf")
    try:
        pdf_bytes = await file.read()
        # print("2.file has been read")
    except Exception as e:
        raise HTTPException(500,detail="couldnt read file")
        #upload in cloudinary
    try:
        upload_result_cloudinary = upload_in_cloudinary(pdf_bytes, file.filename)
    except Exception as e:
        raise HTTPException(500,detail="couldnt upload on cloudinary")
    # print("3.cloudinary done")
    #upload in mongodb
    try : 
        upload_in_mongo = {
            "file_name" : file.filename,
            "file_url" : upload_result_cloudinary.get("secure_url"),
            "public_id": upload_result_cloudinary.get("public_id"),
            "user_id" : user.get("email"),
            "asset_folder" : upload_result_cloudinary.get("asset_folder"),
            "secure_url" : upload_result_cloudinary.get("secure_url"),
            "status" : "processing"
        }
        response = await documets.insert_one(upload_in_mongo) 
        # print("4.file has been uploaded in mongo")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="couldn't upload in mongodb")
    
    # return {
    #     "file_name" : file.filename,
    #     "file_url" : upload_result.get("secure_url"),
    #     "public_id": upload_result.get("public_id"),
    #     "format": upload_result.get("format")
    # }
    
    background_task.add_task(
        process_pdf_in_background,
        doc_id = response.inserted_id,
        pdf_bytes = pdf_bytes,
        filename = file.filename,
        public_id=upload_result_cloudinary.get("public_id"),
        user=user
    )    
    return {
        "message": "File uploaded successfully. Text extraction and embedding is running in the background.",
        "document_id": str(response.inserted_id),
        "status": "processing",
        "file_url": upload_result_cloudinary.get("secure_url")
    }
    

#endpoint to show all the uploaded pdfs by the user
async def get_pdfs(user):
    user_exist = await user_collection.find_one({"email" : user["email"]})
    if not user_exist :
        raise HTTPException(400,detail="user doesnt exist")
    pdfs = await documets.find({"user_id" : user.get("email")}).to_list(length=None)

    if not pdfs:
        return []

    for doc in pdfs:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]

    return pdfs

#endpoint to delete a pdf 
async def delete_pdf(file_id:str,user):
    user_exist = await user_collection.find_one({"email" : user["email"]})
    if not user_exist :
        raise HTTPException(400,detail="user doesnt exist")
    try:
        doc_obj_id = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Document ID format")
    
    file_details = await documets.find_one({"_id" : doc_obj_id})
    if not file_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="file not found")
    try: 
        try:
            delete_qdrant_chunks(file_id,user.get("email"))
        except Exception as q_err:
            print("Qdrant delete warning:", q_err)

        #delete from cloudinary 
        if file_details.get("public_id"):
            try:
                cloudinary.uploader.destroy(file_details.get("public_id"),resource_type="raw")
            except Exception as c_err:
                print("Cloudinary delete warning:", c_err)

        #delete from mongo
        del_mongo = await documets.find_one_and_delete({"_id" : doc_obj_id})
        if not del_mongo:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="could not delete")
        return {"msg" : f"file deleted successfully with id {file_id}"}

    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(500,detail="couldn't delete the file")


# Endpoint service to securely download a user's PDF
async def download_pdf_file(file_id: str, user):
    user_exist = await user_collection.find_one({"email": user["email"]})
    if not user_exist:
        raise HTTPException(status_code=400, detail="User does not exist")
        
    try:
        doc_obj_id = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Document ID format")

    file_doc = await documets.find_one({"_id": doc_obj_id, "user_id": user.get("email")})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")

    public_id = file_doc.get("public_id")
    file_name = file_doc.get("file_name", "document.pdf")
    if not file_name.lower().endswith(".pdf"):
        file_name += ".pdf"

    if not public_id:
        raise HTTPException(status_code=404, detail="File public ID missing")

    try:
        archive_url = cloudinary.utils.download_archive_url(
            public_ids=[public_id],
            resource_type="raw",
            mode="download"
        )
        req = urllib.request.Request(archive_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            zip_bytes = resp.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            names = z.namelist()
            if not names:
                raise HTTPException(status_code=500, detail="Empty archive from storage")
            pdf_bytes = z.read(names[0])

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Download PDF error: {e}")
        raise HTTPException(status_code=500, detail="Could not download PDF from storage")


    




