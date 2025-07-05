# LangChain RAG implementation
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from db.chroma_client import get_vectorstore

def run_rag(question, gemini_client):
    """Run RAG (Retrieval-Augmented Generation) pipeline"""
    try:
        print(f"[DEBUG] RAG: Starting with question: {question}")
        
        # Get vectorstore
        vectorstore = get_vectorstore()
        print(f"[DEBUG] RAG: Got vectorstore")
        
        # Get relevant documents first to see what's retrieved
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        docs = retriever.get_relevant_documents(question)
        print(f"[DEBUG] RAG: Retrieved {len(docs)} documents")
        
        for i, doc in enumerate(docs):
            print(f"[DEBUG] RAG: Document {i+1}: {doc.page_content[:100]}...")
        
        # Create RAG chain
        template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=gemini_client.llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": prompt}
        )
        
        # Get answer
        print(f"[DEBUG] RAG: Invoking QA chain...")
        result = qa_chain.invoke({"query": question})
        answer = result["result"]
        print(f"[DEBUG] RAG: QA chain returned: {answer}")
        return answer
        
    except Exception as e:
        print(f"[DEBUG] RAG Error: {str(e)}")
        return f"[RAG Error] {str(e)}" 