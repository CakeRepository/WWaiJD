"""
RAG Pipeline for What Would AI Jesus Do
Retrieves relevant Bible passages and generates responses using Gemma3:4b
"""

import chromadb
import ollama
from typing import List, Dict


class BibleRAG:
    """RAG pipeline for Bible-based question answering."""
    
    def __init__(self, db_path="chroma_db", top_k=5):
        """
        Initialize the RAG pipeline.
        
        Args:
            db_path: Path to the ChromaDB database
            top_k: Number of relevant passages to retrieve
        """
        self.db_path = db_path
        self.top_k = top_k
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name="bible_kjv")
        
    def generate_query_embedding(self, query: str):
        """Generate embedding for the user's query."""
        try:
            response = ollama.embeddings(model='embeddinggemma', prompt=query)
            return response['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return None
    
    def retrieve_passages(self, query: str) -> List[Dict]:
        """
        Retrieve relevant Bible passages based on the query.
        
        Args:
            query: User's question
            
        Returns:
            List of relevant passages with metadata
        """
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        if query_embedding is None:
            return []
        
        # Query the vector database
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k
        )
        
        # Format results
        passages = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                passages.append({
                    'text': results['documents'][0][i],
                    'reference': results['metadatas'][0][i]['reference'],
                    'book': results['metadatas'][0][i]['book'],
                    'testament': results['metadatas'][0][i]['testament'],
                    'chapter': results['metadatas'][0][i].get('chapter'),
                    'verses': results['metadatas'][0][i].get('verses'),
                    'source_path': results['metadatas'][0][i].get('source_path'),
                    'distance': results['distances'][0][i] if 'distances' in results else 0
                })
        
        return passages
    
    def generate_response(self, query: str, passages: List[Dict]) -> Dict:
        """
        Generate a response using Gemma3:4b based on retrieved passages.
        
        Args:
            query: User's question
            passages: Retrieved Bible passages
            
        Returns:
            Dict with response and source passages
        """
        if not passages:
            return {
                'answer': "I couldn't find relevant passages to answer your question. Please try rephrasing it.",
                'passages': [],
                'error': True
            }
        
        # Build context from passages
        context = "Here are relevant passages from the King James Bible:\n\n"
        for i, passage in enumerate(passages, 1):
            context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
        
        # Create prompt for the model
        prompt = f"""You are AI Jesus, a wise and compassionate guide who provides advice based on Biblical teachings from the King James Bible. A person has asked you a question, and you have been given relevant Bible passages to help answer.

Question: {query}

{context}

Based on these Biblical passages, provide a thoughtful, compassionate response in the voice of Jesus. Your response should:
1. Directly address the question with wisdom and love
2. Reference the specific Bible passages that inform your answer
3. Offer practical guidance while staying true to Biblical teachings
4. Be encouraging and supportive
5. Speak in first person as Jesus would

Response:"""
        
        try:
            # Generate response using Gemma3:4b
            response = ollama.generate(
                model='gemma3:4b',
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                }
            )
            
            return {
                'answer': response['response'].strip(),
                'passages': passages,
                'error': False
            }
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'answer': f"I encountered an error while generating a response. Please make sure the gemma3:4b model is installed (run: ollama pull gemma3:4b)",
                'passages': passages,
                'error': True
            }
    
    def generate_response_stream(self, query: str, passages: List[Dict]):
        """
        Generate a streaming response using Gemma3:4b based on retrieved passages.
        Yields response chunks as they are generated.
        
        Args:
            query: User's question
            passages: Retrieved Bible passages
            
        Yields:
            Dict chunks with response text
        """
        if not passages:
            yield {
                'answer': "I couldn't find relevant passages to answer your question. Please try rephrasing it.",
                'passages': [],
                'error': True,
                'done': True
            }
            return
        
        # Build context from passages
        context = "Here are relevant passages from the King James Bible:\n\n"
        for i, passage in enumerate(passages, 1):
            context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
        
        # Create prompt for the model
        prompt = f"""You are AI Jesus, a wise and compassionate guide who provides advice based on Biblical teachings from the King James Bible. A person has asked you a question, and you have been given relevant Bible passages to help answer.

Question: {query}

{context}

Based on these Biblical passages, provide a thoughtful, compassionate response in the voice of Jesus. Your response should:
1. Directly address the question with wisdom and love
2. Reference the specific Bible passages that inform your answer
3. Offer practical guidance while staying true to Biblical teachings
4. Be encouraging and supportive
5. Speak in first person as Jesus would

Response:"""
        
        try:
            # Generate streaming response using Gemma3:4b
            stream = ollama.generate(
                model='gemma3:4b',
                prompt=prompt,
                stream=True,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                }
            )
            
            # Stream response chunks
            for chunk in stream:
                if chunk.get('response'):
                    yield {
                        'chunk': chunk['response'],
                        'done': chunk.get('done', False),
                        'error': False
                    }
            
            # Send passages at the end
            yield {
                'passages': passages,
                'done': True,
                'error': False
            }
            
        except Exception as e:
            print(f"Error generating streaming response: {e}")
            yield {
                'chunk': f"I encountered an error while generating a response. Please make sure the gemma3:4b model is installed (run: ollama pull gemma3:4b)",
                'passages': passages,
                'error': True,
                'done': True
            }
    
    def ask(self, query: str) -> Dict:
        """
        Main method to ask a question and get an AI Jesus response.
        
        Args:
            query: User's question
            
        Returns:
            Dict with answer, source passages, and metadata
        """
        print(f"\n🙏 Question: {query}")
        
        # Retrieve relevant passages
        print("📖 Retrieving relevant Bible passages...")
        passages = self.retrieve_passages(query)
        print(f"✅ Found {len(passages)} relevant passages")
        
        # Generate response
        print("🤖 Generating AI Jesus response...")
        result = self.generate_response(query, passages)
        print("✅ Response generated")
        
        return result


def main():
    """Test the RAG pipeline."""
    print("=" * 60)
    print("Testing What Would AI Jesus Do RAG Pipeline")
    print("=" * 60)
    
    # Initialize RAG
    try:
        rag = BibleRAG()
        print("✅ RAG pipeline initialized")
    except Exception as e:
        print(f"❌ Error initializing RAG: {e}")
        print("Make sure you've run build_embeddings.py first!")
        return
    
    # Test question
    test_question = "What should I do when someone wrongs me?"
    result = rag.ask(test_question)
    
    print("\n" + "=" * 60)
    print("📜 Answer:")
    print("=" * 60)
    print(result['answer'])
    
    print("\n" + "=" * 60)
    print("📚 Source Passages:")
    print("=" * 60)
    for i, passage in enumerate(result['passages'][:3], 1):
        print(f"\n{i}. {passage['reference']}:")
        print(f"   {passage['text'][:200]}...")


if __name__ == "__main__":
    main()
