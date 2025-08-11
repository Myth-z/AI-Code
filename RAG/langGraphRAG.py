# Cell 1: Imports and Setup
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from dotenv import load_dotenv

# Cross-encoder for reranking
from sentence_transformers import CrossEncoder

load_dotenv()
import dashscope
from dashscope import Generation
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

# Custom LLM class for DashScope
class DashScopeLLM:
    def __init__(self, model="qwen-plus"):
        self.model = model
    
    def __call__(self, prompt: str, **kwargs):
        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                **kwargs
            )
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                return response.output.text
            elif hasattr(response, 'output') and hasattr(response.output, 'choices'):
                return response.output.choices[0].message.content
            else:
                return str(response)
        except Exception as e:
            raise Exception(f"DashScope API error: {str(e)}")
    
    def invoke(self, input_dict: dict):
        if isinstance(input_dict, str):
            prompt = input_dict
        elif isinstance(input_dict, dict):
            prompt = input_dict.get('query', '') or input_dict.get('text', '')
        else:
            prompt = str(input_dict)
        
        return self.__call__(prompt)

# Cell 2: Document Processing
def split_into_chunks(doc_file: str) -> List[Document]:
    """Split document into exactly 10 chunks based on paragraphs"""
    with open(doc_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by double newlines to get paragraphs
    paragraphs = content.split('\n\n')
    
    # Filter out empty paragraphs and clean up
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # If we have more than 10 paragraphs, combine some
    # If we have fewer than 10, split some paragraphs
    if len(paragraphs) > 10:
        # Combine some paragraphs to get exactly 10
        combined_paragraphs = []
        chunks_per_group = len(paragraphs) // 10
        remainder = len(paragraphs) % 10
        
        start_idx = 0
        for i in range(10):
            if i < remainder:
                # First 'remainder' groups get one extra paragraph
                end_idx = start_idx + chunks_per_group + 1
            else:
                end_idx = start_idx + chunks_per_group
            
            combined_text = '\n\n'.join(paragraphs[start_idx:end_idx])
            combined_paragraphs.append(combined_text)
            start_idx = end_idx
        
        chunks = combined_paragraphs
    elif len(paragraphs) < 10:
        # Split some paragraphs to get exactly 10
        chunks = []
        target_chunks = 10
        
        # First, add existing paragraphs
        chunks.extend(paragraphs)
        
        # Then split the longest paragraph(s) to reach 10 chunks
        while len(chunks) < target_chunks:
            # Find the longest chunk to split
            longest_idx = max(range(len(chunks)), key=lambda i: len(chunks[i]))
            longest_chunk = chunks[longest_idx]
            
            # Split the longest chunk in half
            mid_point = len(longest_chunk) // 2
            first_half = longest_chunk[:mid_point]
            second_half = longest_chunk[mid_point:]
            
            # Replace the longest chunk with its halves
            chunks[longest_idx] = first_half
            chunks.insert(longest_idx + 1, second_half)
    else:
        # Exactly 10 paragraphs
        chunks = paragraphs
    
    # Ensure we have exactly 10 chunks
    assert len(chunks) == 10, f"Expected 10 chunks, got {len(chunks)}"
    
    return [Document(page_content=chunk, metadata={"source": doc_file}) for chunk in chunks]

# Cell 3: Reranking Function
def rerank_chunks(query: str, retrieved_chunks: List[str], top_k: int = 3) -> List[str]:
    """Rerank retrieved chunks using Cross-encoder for better relevance"""
    try:
        # Initialize cross-encoder model
        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Create query-chunk pairs for scoring
        pairs = [(query, chunk) for chunk in retrieved_chunks]
        
        # Get relevance scores
        scores = cross_encoder.predict(pairs)
        
        # Pair chunks with scores and sort by score (descending)
        chunk_with_score_list = [(chunk, score) 
                                for chunk, score in zip(retrieved_chunks, scores)]
        chunk_with_score_list.sort(key=lambda pair: pair[1], reverse=True)
        
        # Return top-k reranked chunks
        reranked_chunks = [chunk for chunk, _ in chunk_with_score_list][:top_k]
        
        print(f"Reranking: {len(retrieved_chunks)} chunks → {len(reranked_chunks)} chunks")
        return reranked_chunks
        
    except Exception as e:
        print(f"Reranking failed, using original chunks: {str(e)}")
        return retrieved_chunks[:top_k]

# Cell 4: Vector Database Setup
def setup_vectorstore(chunks: List[Document]) -> Chroma:
    """Setup Chroma vector database with embeddings"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    embeddings = HuggingFaceEmbeddings(
        model_name="shibing624/text2vec-base-chinese",
        model_kwargs={'device': 'cpu'}
    )
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=os.path.join(script_dir, "chroma.db")
    )
    
    return vectorstore

# Cell 5: LangGraph State Definition
from dataclasses import dataclass
from typing import List

@dataclass
class RAGState:
    """State class for the RAG workflow"""
    query: str = ""
    chunks: List[str] = None
    answer: str = ""
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []

# Cell 6: LangGraph Node Functions
def retrieve_chunks(state: RAGState) -> RAGState:
    """Retrieve relevant chunks using two-stage retrieval with reranking"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    vectorstore = Chroma(
        persist_directory=os.path.join(script_dir, "chroma.db"),
        embedding_function=HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese"
        )
    )
    
    # Stage 1: Retrieve more candidates using bi-encoder
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # Retrieve more candidates for reranking
    )
    
    # Get initial candidates
    docs = retriever.invoke(state.query)
    initial_chunks = [doc.page_content for doc in docs]
    
    print(f"Stage 1: Retrieved {len(initial_chunks)} candidate chunks")
    
    # Stage 2: Rerank using Cross-encoder
    reranked_chunks = rerank_chunks(state.query, initial_chunks, top_k=5)
    
    state.chunks = reranked_chunks
    return state

def generate_answer(state: RAGState) -> RAGState:
    """Generate answer using Qwen model"""
    # Create the prompt directly
    prompt = f"""你是一个知识助手，请根据用户提问和下列片段生成准确的回答，口吻要正经严肃，并给出信息源。

用户问题：{state.query}

相关片段：
{chr(10).join(state.chunks)}

请基于上列信息回答问题，不要编造虚假信息。"""
    
    # Use the DashScope LLM directly
    llm = DashScopeLLM(model="qwen-plus")
    result = llm(prompt)
    
    state.answer = result
    return state

# Cell 7: LangGraph Workflow
def create_rag_workflow():
    """Create the RAG workflow using LangGraph"""
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_chunks)
    workflow.add_node("generate", generate_answer)
    
    # Define the flow
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

# Cell 8: Main Execution
def main():
    """Main function to run the RAG system"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Process document
    doc_path = os.path.join(script_dir, "doc.md")
    chunks = split_into_chunks(doc_path)
    print(f"Split document into {len(chunks)} chunks")
    
    print("Setting up vector database...")
    
    # Clear existing database and setup vector database
    import shutil
    db_path = os.path.join(script_dir, "chroma.db")
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        shutil.rmtree(db_path)
    
    print("Setting up fresh vector database...")
    vectorstore = setup_vectorstore(chunks)
    print("Vector database setup complete")
    
    # Verify database setup
    all_docs = vectorstore.get()
    print(f"Database ready with {len(all_docs['documents'])} documents")
    
    # Create and run workflow
    rag_workflow = create_rag_workflow()
    
    # Test query
    query = "哆啦A梦使用的3个秘密道具是什么？"
    print(f"\nQuery: {query}")
    
    print("\nRunning RAG workflow...")
    
    # Run workflow
    result = rag_workflow.invoke({"query": query})
    
    # Display results
    print(f"\nRetrieved chunks: {len(result['chunks'])}")
    for i, chunk in enumerate(result['chunks']):
        print(f"[{i}] {chunk[:100]}...")
    
    print(f"\nAnswer: {result['answer']}")

# Cell 8: Alternative LangChain RAG Chain
def create_simple_rag_chain():
    """Create a simple RAG chain using LangChain"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    vectorstore = Chroma(
        persist_directory=os.path.join(script_dir, "chroma.db"),
        embedding_function=HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese"
        )
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    prompt_template = """你是一个知识助手，请根据用户提问和下列片段生成准确的回答，口吻要正经严肃，并给出信息源。

用户问题：{question}

相关片段：
{context}

请基于上列信息回答问题，不要编造虚假信息。"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question", "context"]
    )
    
    llm = DashScopeLLM(model="qwen-plus")
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt}
    )
    
    return qa_chain

# Cell 9: Test Simple RAG Chain
def test_simple_rag():
    """Test the simple RAG chain"""
    qa_chain = create_simple_rag_chain()
    
    query = "哆啦A梦使用的3个秘密道具是什么？"
    print(f"Query: {query}")
    
    result = qa_chain.invoke({"query": query})
    print(f"Answer: {result['result']}")

# Run the main function
if __name__ == "__main__":
    main()