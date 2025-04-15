from flask import Flask, render_template, jsonify, request, session
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.prompt import *
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = os.urandom(24)

# Load environment variables from .env file
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["TOGETHER_API_KEY"] = TOGETHER_API_KEY
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN

# Initialize Hugging Face model and Pinecone embeddings
embeddings = download_hugging_face_embeddings()

index_name = "medicalbot"

# Set up Pinecone Vector Store
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
)

# Setup retriever for document search
retriver = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# Initialize the Hugging Face language model
llm = ChatOpenAI(
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key=os.getenv("TOGETHER_API_KEY"),
    model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.5,
    max_tokens=512,
)

system_prompt = (
    "You are MedBot, a helpful and concise assistant that answers medical questions clearly and directly."
    "Use the retrieved context to answer the user's question. If the exact answer is not found, make your best educated guess"
    "based on common medical knowledge. Do not mention missing context or apologize. Avoid disclaimers. Keep responses short and helpful."
    "If the answer contains multiple steps, recommendations, or types of information, present it in a clean, organized format:\n"
    "- Use numbered or bullet-point lists where appropriate.\n"
    "- Bold important terms or headings using Markdown (like **Recovery**, **Side Effects**).\n"
    "- Use short paragraphs if listing isn't suitable.\n"
    "Keep the response short, clear, and easy to scan.\n"
    "\n\n"
    "{context}"
)

# Setup prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Create the chain for question-answering
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriver, question_answer_chain)

# Flask route for the index page (render HTML frontend)
@app.route('/')
def index():
    return render_template('index.html')

# Flask route to handle the chatbot messages
@app.route('/get', methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "msg" not in data:
            return jsonify({"response": "Invalid request, no message found"}), 400

        msg = data["msg"]
        print(f"Received message: {msg}")

        # Check if we have a session and create the conversation history
        if "conversation_history" not in session:
            session["conversation_history"] = []

        # Add user message to conversation history
        session["conversation_history"].append(f"User: {msg}")

        # Keep only the last 6 lines (3 user + 3 bot turns)
        recent_history = session["conversation_history"][-10:]
        conversation_history = "\n".join(recent_history) + "\nBot:"


        # Make the API call
        response = rag_chain.invoke({"input": conversation_history})
        answer = response['answer']

        # Remove unwanted phrases
        unwanted_phrases = [
            "Acne is not mentioned in the provided context",
            "Based on the provided context",
            "The text provided discusses",
            "The provided context discusses treatments for contact dermatitis, not acne.",
            "Based on the context provided, it is not possible to make a definitive diagnosis about your condition."
        ]

        for phrase in unwanted_phrases:
            answer = answer.replace(phrase, "")

        answer = " ".join(answer.split())
        print(f"Final Answer: {answer}")

        # Add bot response to conversation history
        session["conversation_history"].append(f"Bot: {answer}")

        # Return the bot's response
        return jsonify({"response": answer})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "An error occurred, please try again later"}), 500

# Start the Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
