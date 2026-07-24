from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz
from fastapi import UploadFile
# from langchain_chroma import Chroma
from utils.qdrant_config import vectorStore
import traceback
#load the document
def extract_text(pdf_bytes):
    docs = fitz.open(stream=pdf_bytes,filetype="pdf")
    text = "\n".join(str(page.get_text()) for page in docs)
    docs.close()
    return text 

def split_text(text,file: UploadFile,inserted_id,cloudinary_public_id,user):
    splitter  = RecursiveCharacterTextSplitter(chunk_size=3000,chunk_overlap=200)
    documents = splitter.create_documents(
        [text],
        metadatas=[{
            "filename": file.filename,
            "mongo_id": str(inserted_id),
            "public_id": cloudinary_public_id,
            "user_email" : user.get("email")
        }]
    )
    
    # docs = []
    # for st in splitted_text:
    #     docs.append(
    #         Document(page_content=st)
    #     )
    # embed = GoogleGenerativeAIEmbeddings(model='gemini-embedding-2')
    # vectorStore = Chroma(collection_name='sample',persist_directory='./sample_chromaDB',embedding_function=embed)


    try:
        print("Adding documents...")
        vectorStore.add_documents(documents)
        print("Done")
    except Exception:
        traceback.print_exc()
    return documents