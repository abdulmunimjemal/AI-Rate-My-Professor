import os
from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from rag import RAG

class ProfessorRaterAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Pinecone Setup
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        if self.PINECONE_API_KEY is None:
            raise ValueError("Please set the PINECONE_API_KEY environment variable")

        # Initialize Pinecone client and embeddings
        self.pc_client = Pinecone(api_key=self.PINECONE_API_KEY)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.index_name = "professors-index"

        # Initialize RAG with Pinecone client, index, and embeddings
        self.rag = RAG(self.pc_client, self.index_name, self.embeddings)

        # Initialize retriever
        self.retriever = self.rag.get_retriever()

        # Initialize LLM (Language Model)
        self.llm = ChatOpenAI(model="gpt-4o-mini")

        # System prompt for contextualizing questions
        self.contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, just "
            "reformulate it if needed and otherwise return it as is."
        )

        # Create a prompt template for contextualizing questions
        self.contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # Create history aware retriever
        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, self.contextualize_q_prompt
        )

        # System prompt for answering questions
        self.qa_system_prompt = (
            """
            You are a Professor Rater Bot.  
            Use the following pieces of retrieved context to list the professors that fulfill the user's requirement.
            If no related professors are found in the context, respond politely that you couldn't find such professors and that we are working on improving more.
            \n\n
            {context}
            """
        )

        # Create a prompt template for the QA system
        self.qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # Create a chain for question answering
        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)

        # Create a retrieval chain using the history-aware retriever and QA chain
        self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.question_answer_chain)

    def invoke(self, input: str, chat_history: list):
        """Invoke the retrieval chain with the provided input and chat history.

        Args:
            input (str): The user input or query.
            chat_history (list): A list of messages representing the chat history.

        Returns:
            str: The AI's response text.
        """
        # Process the user's query through the retrieval chain
        result = self.rag_chain.invoke({"input": input, "chat_history": chat_history})
        return result['answer']


# Example usage to start the continual chat
def start_chat(bot: ProfessorRaterAgent):
    """Start a continual chat session with the AI."""
    print("Start chatting with the AI! Type 'exit' to end the conversation.")
    chat_history = []  # Collect chat history here (a sequence of messages)
    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break
        # Invoke the bot with the user's query and chat history
        answer = bot.invoke(query, chat_history)
        # Display the AI's response
        print(f"AI: {answer}")
        # Update the chat history
        chat_history.append(HumanMessage(content=query))
        chat_history.append(SystemMessage(content=answer))


# Main function to start the continual chat
if __name__ == "__main__":
    bot = ProfessorRaterAgent()
    start_chat(bot)