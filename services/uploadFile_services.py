from utils.cloudinary_config import cloudinary_config
import cloudinary.uploader 
from fastapi import UploadFile,File,HTTPException ,status
from db.database import documets,user_collection
import io
from utils.vector_store import extract_text,split_text
from utils.upload_cloudinary import upload_in_cloudinary
from schemas.users import authMW
cloudinary_config()
async def upload_file(user ,file: UploadFile = File(...)):
    # print(user)
    user_exist = await user_collection.find_one({"email" : user["email"]})
    if not user_exist :
        raise HTTPException(400,detail="user doesnt exist")
    print("1.user verified")
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="file type should be pdf")
    try:
        pdf_bytes = await file.read()
        print("2.file has been read")
    except Exception as e:
        raise HTTPException(500,detail="couldnt read file")
        #upload in cloudinary
    try:
        upload_result_cloudinary = upload_in_cloudinary(pdf_bytes)
    except Exception as e:
        raise HTTPException(500,detail="couldnt upload on cloudinary")
    print("3.cloudinary done")
    #upload in mongodb
    try : 
        upload_in_mongo = {
            "file_name" : file.filename,
            "file_url" : upload_result_cloudinary.get("secure_url"),
            "public_id": upload_result_cloudinary.get("public_id"),
            "asset_folder" : upload_result_cloudinary.get("asset_folder"),
            "secure_url" : upload_result_cloudinary.get("secure_url"),
            "tags" : upload_result_cloudinary.get("tags")
        }
        response = await documets.insert_one(upload_in_mongo) 
        print("4.file has been uploaded in mongo")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="couldn't upload in mongodb")
    
    # return {
    #     "file_name" : file.filename,
    #     "file_url" : upload_result.get("secure_url"),
    #     "public_id": upload_result.get("public_id"),
    #     "format": upload_result.get("format")
    # }
    
    #call to utils for parsing
    try:
        text = extract_text(pdf_bytes)
        print("5.text extracted")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="couldn't parse the text")
    
    #for chunking and embedding 
    try:
        splitted_text = split_text(text,file,response.inserted_id,upload_result_cloudinary.get("public_id"))
        print("5.text splitted and embedded")
    except Exception as e:
        raise HTTPException(500,detail="couldnt generate embedding")
    
    return {
        "response" : str(response.inserted_id),
        "text" : splitted_text
    }
