from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from utils.qdrant_config import client, COLLECTION_NAME
from fastapi import HTTPException

def delete_qdrant_chunks(mongo_id: str, user_email: str):
    try: 
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.mongo_id",
                        match=MatchValue(value=mongo_id)
                    ),
                    FieldCondition(
                        key="metadata.user_email",
                        match=MatchValue(value=user_email)
                    )
                ]
            )
        )
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500,detail="couldn't delete from qdrant")