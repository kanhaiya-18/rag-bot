from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from core.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import PayloadSchemaType

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    prefer_grpc=False,
    timeout=60.0,
)
COLLECTION_NAME = "documents"

collections = client.get_collections().collections

if COLLECTION_NAME not in [c.name for c in collections]:
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=768,
            distance=Distance.COSINE,
        ),
    )
    

try:
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="metadata.user_email",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="metadata.mongo_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
except Exception as e:
    print(e)


# info = client.get_collection("documents_v2")
# print(info.config.params.vectors)
embed = GoogleGenerativeAIEmbeddings(
    model='gemini-embedding-2',
    google_api_key=settings.GOOGLE_API_KEY,
    output_dimensionality=768,
)
vectorStore = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embed,
)
