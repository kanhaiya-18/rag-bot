from fastapi import HTTPException,status
from utils.llm import model
from langchain_core.messages import HumanMessage
from uuid import uuid4
from db.database import user_collection,chat_collection
from datetime import datetime,UTC
import psycopg
from core.config import settings

async def ask_question(graph,user, question):

    user_exist = await user_collection.find_one(
        {
            "email": user["email"]
        }
    )
    if not user_exist:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
    is_new_chat = False
    if question.thread_id:
        thread_id = question.thread_id
        chat = await chat_collection.find_one({"thread_id": thread_id, "user_email": user["email"]})
        if not chat:
            raise HTTPException(status_code=404, detail="Chat thread not found")
        
        title = chat.get("title", "")
        # Update thread timestamp
        await chat_collection.update_one(
            {"thread_id": thread_id},
            {"$set": {"updated_at": datetime.now(UTC)}}
        )
    else:
        thread_id = str(uuid4())
        prompt_for_title = f"""give a title to the context dont write anything else because im writing the same thing that you are 
        gonna respond , and write the topic's title name only that too in maximum 3-4 words : \n {question.question}"""
        response_from_llm = model.invoke(prompt_for_title)
        title = response_from_llm.content[0]['text']  # type: ignore

        await chat_collection.insert_one({
            "thread_id": thread_id,
            "title": title,
            "user_email": user["email"],
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = await graph.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=question.question
                )
            ],
            "user_email": user["email"]
        },
        config=config
    )
    return {
        "thread_id": thread_id,
        "title" : title,
        "answer": result["messages"][-1].content
    }

#endpoint to get all the threads for the sidebar
async def get_users_chat(user):
    user_exist = await user_collection.find_one(
            {
                "email": user.get("email")
            }
        )
    if not user_exist:
        raise HTTPException(status_code=401,detail="Unauthorized user")
    try:
        chats = await chat_collection.find({"user_email" : user.get("email")},{"_id": 0}).sort("updated_at",-1).to_list(length=None)
        return chats if chats else []
    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,detail="something went wrong")

#get the chats of particular thread_id
async def get_history(graph,thread_id:str,user):
    user_exist = await user_collection.find_one(
                {
                    "email": user.get("email")
                }
            )
    if not user_exist:
        raise HTTPException(status_code=401,detail="Unauthorized user")

    is_thread_id = await chat_collection.find_one({"thread_id" : thread_id})
    if not is_thread_id :
        raise HTTPException(status.HTTP_404_NOT_FOUND,detail="chat session doesnt exist")

    config = {"configurable" : {"thread_id" : thread_id}}
    state = await graph.aget_state(config)
    messages = []
    if state and state.values and "messages" in state.values:
        for msg in state.values["messages"]:
            messages.append({
                "role": "user" if msg.type in ("human", "user") else "assistant",
                "content": msg.content
            })
    return {
        "thread_id": thread_id,
        "messages": messages
    }
    

async def delete_chat(thread_id: str, user):
    user_exist = await user_collection.find_one({"email": user.get("email")})
    if not user_exist:
        raise HTTPException(status_code=401, detail="Unauthorized user")
    
    chat_session = await chat_collection.find_one({
        "thread_id": thread_id,
        "user_email": user.get("email")
    })
    if not chat_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    # 1. Delete thread document from MongoDB
    await chat_collection.delete_one({"thread_id": thread_id, "user_email": user.get("email")})

    # 2. Delete thread checkpoints from PostgreSQL
    try:
        async with await psycopg.AsyncConnection.connect(settings.POSTGRES_URL) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
                await cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
                await cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
                await conn.commit()
    except Exception as pg_err:
        print(f"PostgreSQL checkpoint deletion warning for thread {thread_id}:", pg_err)

    return {"msg": "Chat deleted successfully", "thread_id": thread_id}

async def rename_chat(thread_id: str, new_title: str, user):
    user_exist = await user_collection.find_one({"email": user.get("email")})
    if not user_exist:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    chat_session = await chat_collection.find_one({
        "thread_id": thread_id,
        "user_email": user.get("email")
    })
    if not chat_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    await chat_collection.update_one(
        {"thread_id": thread_id, "user_email": user.get("email")},
        {"$set": {"title": new_title, "updated_at": datetime.now(UTC)}}
    )
    return {"msg": "Chat renamed successfully", "thread_id": thread_id, "title": new_title}
    