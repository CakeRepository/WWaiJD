"""
RAG Pipeline for What Would AI Jesus Do
Retrieves relevant Bible passages and generates responses using Gemma3:4b
"""

import os
import chromadb
import ollama
from typing import List, Dict, Optional, Generator, Any, Union

# Focus modes allow the caller to steer tone and structure without changing the UX copy.
MODE_INSTRUCTIONS = {
    'balanced': 'Respond with a balanced mix of empathy and clear guidance. Keep the tone warm and concise.',
    'comfort': 'Respond with extra gentleness and reassurance. Emphasize God\'s nearness and peace.',
    'clarity': 'Respond with direct, practical steps and short sentences. Provide a concise roadmap.',
    'challenge': 'Respond with loving conviction, calling the reader toward obedience and change.',
    'blessing': 'Respond briefly with encouragement plus a short closing prayer rooted in the cited verses.'
}
DEFAULT_MODE = 'balanced'
DEFAULT_EMBED_MODEL = 'embeddinggemma'
DEFAULT_LLM_MODEL = 'gemma3:4b'
DEFAULT_EMBED_KEEP_ALIVE = os.getenv('WWAIJD_EMBED_KEEP_ALIVE', '0s')
DEFAULT_LLM_KEEP_ALIVE = os.getenv('WWAIJD_LLM_KEEP_ALIVE', '120s')


class BibleRAG:
    """RAG pipeline for Bible-based question answering."""
    
    def __init__(
        self,
        db_path: str = "chroma_db",
        top_k: int = 5,
        embedding_model: str = DEFAULT_EMBED_MODEL,
        llm_model: str = DEFAULT_LLM_MODEL,
        embed_keep_alive: Optional[Union[str, float]] = None,
        llm_keep_alive: Optional[Union[str, float]] = None,
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            db_path: Path to the ChromaDB database directory. Defaults to "chroma_db".
            top_k: Number of relevant passages to retrieve for each query. Defaults to 5.
            embedding_model: Name of the Ollama embedding model. Defaults to "embeddinggemma".
            llm_model: Name of the Ollama generation model. Defaults to "gemma3:4b".
            embed_keep_alive: Duration to keep the embedding model loaded in VRAM (e.g., '5m', 300).
                Defaults to '0s' (immediate unload) to save resources.
            llm_keep_alive: Duration to keep the LLM loaded in VRAM. Defaults to '120s'.
        """
        self.db_path = db_path
        self.top_k = top_k
        self.embedding_model = embedding_model or DEFAULT_EMBED_MODEL
        self.llm_model = llm_model or DEFAULT_LLM_MODEL
        self.embed_keep_alive = DEFAULT_EMBED_KEEP_ALIVE if embed_keep_alive is None else embed_keep_alive
        self.llm_keep_alive = DEFAULT_LLM_KEEP_ALIVE if llm_keep_alive is None else llm_keep_alive
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name="bible_kjv")
        
    def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Generate a vector embedding for the user's query.

        Args:
            query: The user's input text.

        Returns:
            Optional[List[float]]: The embedding vector if successful, None otherwise.
        """
        try:
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=query,
                keep_alive=self.embed_keep_alive
            )
            return response['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return None
    
    def retrieve_passages(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant Bible passages based on the query.
        
        Uses the embedding model to convert the query to a vector and finds
        semantically similar passages in the ChromaDB collection.

        Args:
            query: The user's question or search term.
            
        Returns:
            List[Dict[str, Any]]: A list of relevant passages. Each dictionary contains:
                - text: The verse text.
                - reference: Book Chapter:Verses.
                - book: Book name.
                - testament: Old or New Testament.
                - chapter: Chapter number.
                - verses: Verse range.
                - source_path: Relative path to source file.
                - distance: Vector distance score.
                - relevance: Normalized relevance score (0-100).
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
        distances = results['distances'][0] if results and 'distances' in results else []
        normalized_scores = self._normalize_relevance(distances)
        
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
                    'distance': results['distances'][0][i] if 'distances' in results else 0,
                    'relevance': normalized_scores[i] if normalized_scores else None
                })
        
        return passages
    
    def _normalize_relevance(self, distances: List[float]) -> List[float]:
        """
        Convert raw vector distances into a relative 0-100 relevance score.

        This helps the UI display confidence without exposing raw distance metrics.
        Lower distance means higher relevance.

        Args:
            distances: A list of float distances from ChromaDB.

        Returns:
            List[float]: A list of normalized scores from 0.0 to 100.0.
        """
        if not distances:
            return []
        try:
            min_distance = min(distances)
            max_distance = max(distances)
            if max_distance == min_distance:
                return [100.0 for _ in distances]
            scores = []
            for value in distances:
                normalized = 1 - ((value - min_distance) / (max_distance - min_distance))
                scores.append(round(max(0.0, min(1.0, normalized)) * 100, 1))
            return scores
        except Exception:
            return []
    
    def _normalize_mode(self, mode: Optional[str]) -> str:
        """
        Map a provided mode string to a supported key in MODE_INSTRUCTIONS.

        Args:
            mode: The requested mode (e.g., "Comfort", "balanced").

        Returns:
            str: The normalized mode key (e.g., "comfort").
                 Returns DEFAULT_MODE if the input is invalid or None.
        """
        if not mode:
            return DEFAULT_MODE
        mode_key = mode.strip().lower()
        return mode_key if mode_key in MODE_INSTRUCTIONS else DEFAULT_MODE
    
    def _build_prompt(self, query: str, passages: List[Dict], mode: str) -> str:
        """
        Construct the chat prompt with retrieved passages and the requested tone.

        Args:
            query: The user's question.
            passages: A list of retrieved passage dictionaries.
            mode: The normalized mode key determining the tone.

        Returns:
            str: The fully formatted prompt string ready for the LLM.
        """
        tone_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS[DEFAULT_MODE])
        
        context = "Here are relevant passages from the King James Bible:\n\n"
        for i, passage in enumerate(passages, 1):
            context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
        
        return f"""You are AI Jesus, a wise and compassionate guide who provides advice based on Biblical teachings from the King James Bible. A person has asked you a question, and you have been given relevant Bible passages to help answer.

Question: {query}

{context}

Guidance: {tone_instruction}

Based on these Biblical passages, provide a thoughtful response in the voice of Jesus. Please:
- Reference the specific Bible passages that inform your answer (e.g., cite book and verse inline).
- Stay grounded in the provided passages; avoid inventing references.
- Offer practical guidance that can be acted on today.
- Keep the answer under about 180 words unless brevity would harm clarity.
- If passages seem weakly related, briefly acknowledge that and invite the reader to explore the cited verses.

Response:"""
    
    def generate_response(self, query: str, passages: List[Dict], mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete response using the LLM based on retrieved passages.
        
        This is a blocking call that waits for the full response.

        Args:
            query: The user's question.
            passages: The list of retrieved Bible passages.
            mode: Optional focus mode for tone/structure.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - answer: The generated text response.
                - passages: The input passages.
                - error: Boolean indicating if an error occurred.
                - mode: The mode used.
        """
        selected_mode = self._normalize_mode(mode)

        if not passages:
            return {
                'answer': "I couldn't find relevant passages to answer your question. Please try rephrasing it.",
                'passages': [],
                'error': True,
                'mode': selected_mode
            }
        
        prompt = self._build_prompt(query, passages, selected_mode)
        
        try:
            # Generate response using Gemma3:4b
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                },
                keep_alive=self.llm_keep_alive
            )
            
            return {
                'answer': response['response'].strip(),
                'passages': passages,
                'error': False,
                'mode': selected_mode
            }
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'answer': f"I encountered an error while generating a response. Please make sure the {self.llm_model} model is installed (run: ollama pull {self.llm_model})",
                'passages': passages,
                'error': True,
                'mode': selected_mode
            }

    def ask(self, query: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Convenience wrapper that retrieves passages then generates a response.

        Combines `retrieve_passages` and `generate_response`.

        Args:
            query: The user's question.
            mode: Optional focus mode.

        Returns:
            Dict[str, Any]: The response dictionary (see `generate_response`).
        """
        passages = self.retrieve_passages(query)
        return self.generate_response(query, passages, mode=mode)
    
    def generate_response_stream(
        self,
        query: str,
        passages: List[Dict],
        mode: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming response using the LLM based on retrieved passages.
        
        Yields response chunks as they are generated, allowing for real-time UI updates.

        Args:
            query: The user's question.
            passages: The list of retrieved Bible passages.
            mode: Optional focus mode for tone/structure.

        Yields:
            Dict[str, Any]: Chunks of the response.
                - chunk: The text fragment.
                - done: Boolean indicating completion.
                - error: Boolean indicating error.
                - mode: The mode used.
                - passages: (Final chunk only) The passages used.
        """
        selected_mode = self._normalize_mode(mode)

        if not passages:
            yield {
                'answer': "I couldn't find relevant passages to answer your question. Please try rephrasing it.",
                'passages': [],
                'error': True,
                'done': True,
                'mode': selected_mode
            }
            return
        
        prompt = self._build_prompt(query, passages, selected_mode)
        
        try:
            # Generate streaming response using Gemma3:4b
            stream = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                stream=True,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                },
                keep_alive=self.llm_keep_alive
            )
            
            # Stream response chunks
            for chunk in stream:
                if chunk.get('response'):
                    yield {
                        'chunk': chunk['response'],
                        'done': chunk.get('done', False),
                        'error': False,
                        'mode': selected_mode
                    }
            
            # Send passages at the end
            yield {
                'passages': passages,
                'done': True,
                'error': False,
                'mode': selected_mode
            }
            
        except Exception as e:
            print(f"Error in streaming response: {e}")
            yield {
                'error': str(e),
                'done': True,
                'mode': selected_mode
            }

    def generate_study(self, topic: str) -> Dict[str, Any]:
        """
        Generate a thematic Bible study based on a topic.

        Retrieves passages related to the topic and instructs the LLM to
        create a structured study with introduction, key verses, reflection, and prayer.

        Args:
            topic: The topic for the Bible study.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - study: The generated study text.
                - passages: The passages used.
                - error: Boolean indicating success/failure.
        """
        passages = self.retrieve_passages(topic)
        
        if not passages:
            return {
                'study': "I couldn't find relevant passages for this topic. Please try a different one.",
                'passages': [],
                'error': True
            }
            
        context = "Here are relevant passages:\n\n"
        for i, passage in enumerate(passages, 1):
            context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
            
        prompt = f"""You are AI Jesus, a wise teacher. Create a short Bible study on the topic: "{topic}".
        
{context}

Structure the study as follows:
1. **Introduction**: Briefly introduce the topic.
2. **Key Verses**: Discuss 2-3 of the provided verses and their meaning.
3. **Reflection**: Ask 2-3 questions to help the reader apply this to their life.
4. **Prayer**: A short closing prayer.

Keep the tone encouraging and insightful.
"""
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={'temperature': 0.7},
                keep_alive=self.llm_keep_alive
            )
            return {
                'study': response['response'].strip(),
                'passages': passages,
                'error': False
            }
        except Exception as e:
            print(f"Error generating study: {e}")
            return {'study': "Error generating study.", 'error': True}

    def generate_prayer(self, request: str) -> Dict[str, Any]:
        """
        Generate a personalized prayer based on a user request.

        Retrieves relevant verses to inspire the prayer content.

        Args:
            request: The user's prayer request.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - prayer: The generated prayer text.
                - passages: The passages used for inspiration.
                - error: Boolean indicating success/failure.
        """
        passages = self.retrieve_passages(request)
        
        context = ""
        if passages:
            context = "Here are some relevant verses to inspire the prayer:\n\n"
            for i, passage in enumerate(passages[:3], 1):
                context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
        
        prompt = f"""You are AI Jesus. A user has asked for prayer: "{request}".
        
{context}

Write a heartfelt, comforting prayer for them. 
- Address their specific situation.
- Weave in the themes from the verses if applicable.
- Keep it under 150 words.
- End with "Amen."
"""
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={'temperature': 0.8},
                keep_alive=self.llm_keep_alive
            )
            return {
                'prayer': response['response'].strip(),
                'passages': passages,
                'error': False
            }
        except Exception as e:
            print(f"Error generating prayer: {e}")
            return {'prayer': "Error generating prayer.", 'error': True}


def main():
    """
    Test the RAG pipeline with a sample question.

    Initializes the pipeline and asks "What should I do when someone wrongs me?".
    Prints the answer and source passages.
    """
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
