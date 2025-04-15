from src.helper import load_pdf_file, text_split
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")  # Add Together API key

# Extract text data from PDFs
extracted_data = load_pdf_file(data="Data/")
text_chunks = text_split(extracted_data)

# No need for Hugging Face embeddings. Proceed with your regular embeddings method.
# Use Pinecone for text embeddings if you're using a pre-built model or another library.
# Example: Update with Mixtral or another embedding method if needed.
from langchain.embeddings import OpenAIEmbeddings  # Example, replace if necessary
embeddings = OpenAIEmbeddings()

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "medicalbot"

# Create Pinecone index if not already created
pc.create_index(
    name=index_name,
    dimension=384,  # Ensure this matches your embedding size
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)

# Store the documents into the Pinecone vector store
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings,
)
