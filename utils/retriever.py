from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from utils.qdrant_config import vectorStore


def get_retriever(email: str):

    return vectorStore.as_retriever(
        search_kwargs={
            "k": 4,
            "filter": Filter(
                must=[
                    FieldCondition(
                        key="metadata.user_email",
                        match=MatchValue(value=email)
                    )
                ]
            )
        }
    )