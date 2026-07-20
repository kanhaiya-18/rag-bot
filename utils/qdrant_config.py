from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from core.config import settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore


client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
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


# info = client.get_collection("documents_v2")
# print(info.config.params.vectors)
embed = GoogleGenerativeAIEmbeddings(model='gemini-embedding-2',output_dimensionality=768)
# print(embed.model)
vectorStore = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embed,
)
