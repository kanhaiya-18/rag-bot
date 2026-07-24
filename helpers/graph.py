from typing_extensions import TypedDict
from typing import Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain_core.messages import AnyMessage, AIMessage

from utils.llm import model
from utils.retriever import get_retriever


class ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_email: str

def chatbot(state: ChatState):

    question = state["messages"][-1].content

    retriever = get_retriever(state["user_email"])

    docs = retriever.invoke(question)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    history = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in state["messages"][:-1]
    )

    prompt = f"""
        You are a helpful assistant.

        Conversation History:
        {history}

        Context:
        {context}

        Question:
        {question}
    """

    response = model.invoke(prompt)

    return {
        "messages": [
            AIMessage(content=response.content[0]['text'])
        ]
    }


builder = StateGraph(ChatState)

builder.add_node("chatbot", chatbot)

builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)