from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
from utils.qdrant_config import vectorStore


def get_retriever(email: str, mongo_ids: list[str] | None = None):

    must_conditions = [
        FieldCondition(
            key="metadata.user_email",
            match=MatchValue(value=email)
        )
    ]

    # If specific docs are selected, narrow the search to only those
    if mongo_ids:
        must_conditions.append(
            FieldCondition(
                key="metadata.mongo_id",
                match=MatchAny(any=mongo_ids)
            )
        )

    return vectorStore.as_retriever(
        search_kwargs={
            "k": 4,
            "filter": Filter(must=must_conditions)
        }
    )