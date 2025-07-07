"""
Test script for document preprocessor
"""
import os
import logging
from dotenv import load_dotenv
from services.document_preprocessor import DocumentPreprocessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_document_preprocessor():
    """Test the document preprocessor with sample group chat data"""
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not set")
        return
    
    # Initialize preprocessor
    preprocessor = DocumentPreprocessor(api_key)
    
    # Sample group chat documents
    sample_documents = [
        {
            "content": """
[2024-01-15 10:30:15] Alice: Good morning everyone! 
[2024-01-15 10:30:45] Bob: Morning Alice! How's it going?
[2024-01-15 10:31:00] Alice: Pretty good! Working on the new project
[2024-01-15 10:31:15] Bob: Nice! What's the timeline looking like?
[2024-01-15 10:31:30] Alice: We're aiming for end of February
[2024-01-15 10:31:45] Bob: That sounds doable
[2024-01-15 10:32:00] Charlie: haha 😂
[2024-01-15 10:32:15] Alice: Charlie, any updates on the backend?
[2024-01-15 10:32:30] Charlie: Yeah, API is ready for testing
[2024-01-15 10:32:45] Alice: Perfect! Let's schedule a demo
[2024-01-15 10:33:00] Bob: I'm in
[2024-01-15 10:33:15] Charlie: 👍
"""
        },
        {
            "content": """
[2024-01-16 14:20:00] David: Hey team, we need to discuss the budget
[2024-01-16 14:20:30] Alice: Sure, what's the issue?
[2024-01-16 14:21:00] David: We're over by 15% on development costs
[2024-01-16 14:21:30] Bob: That's concerning. What's driving it?
[2024-01-16 14:22:00] David: Mostly the cloud infrastructure scaling
[2024-01-16 14:22:30] Alice: We need to optimize that
[2024-01-16 14:23:00] Charlie: lol budget problems again
[2024-01-16 14:23:30] David: This is serious Charlie
[2024-01-16 14:24:00] Alice: Let's have a meeting tomorrow at 2 PM
[2024-01-16 14:24:30] Bob: Works for me
[2024-01-16 14:25:00] David: I'll send calendar invites
[2024-01-16 14:25:30] Charlie: ok whatever
"""
        },
        {
            "content": """
[2024-01-17 09:15:00] Alice: Meeting reminder - budget discussion at 2 PM today
[2024-01-17 09:15:30] Bob: Got it
[2024-01-17 09:16:00] David: Thanks Alice
[2024-01-17 09:16:30] Charlie: 👍
[2024-01-17 14:00:00] Alice: Starting the budget meeting now
[2024-01-17 14:00:30] David: Thanks everyone for joining
[2024-01-17 14:01:00] David: As I mentioned, we're 15% over budget
[2024-01-17 14:01:30] Bob: What are our options to reduce costs?
[2024-01-17 14:02:00] David: We can switch to cheaper cloud providers
[2024-01-17 14:02:30] Alice: That might affect performance
[2024-01-17 14:03:00] Bob: We could also optimize our code
[2024-01-17 14:03:30] Charlie: haha good luck with that
[2024-01-17 14:04:00] Alice: Charlie, please stay focused
[2024-01-17 14:04:30] David: Let's implement both strategies
[2024-01-17 14:05:00] Bob: Agreed
[2024-01-17 14:05:30] Alice: Meeting adjourned
"""
        }
    ]
    
    logger.info("🧪 Testing document preprocessor...")
    logger.info(f"📄 Processing {len(sample_documents)} sample documents")
    
    # Process documents
    try:
        preprocessed_docs = preprocessor.preprocess_documents(sample_documents)
        
        logger.info(f"✅ Preprocessing completed!")
        logger.info(f"📊 Results:")
        
        total_original = sum(len(doc.get('content', '')) for doc in sample_documents)
        total_processed = sum(len(doc.get('content', '')) for doc in preprocessed_docs)
        
        logger.info(f"   - Original documents: {len(sample_documents)}")
        logger.info(f"   - Processed documents: {len(preprocessed_docs)}")
        logger.info(f"   - Total original characters: {total_original}")
        logger.info(f"   - Total processed characters: {total_processed}")
        logger.info(f"   - Overall compression: {total_processed/total_original:.1%}")
        
        # Show sample results
        for i, doc in enumerate(preprocessed_docs):
            logger.info(f"\n📄 Document {i+1}:")
            logger.info(f"   - Original length: {doc.get('original_length', 'N/A')}")
            logger.info(f"   - Processed length: {doc.get('processed_length', 'N/A')}")
            logger.info(f"   - Compression ratio: {doc.get('compression_ratio', 'N/A'):.1%}")
            logger.info(f"   - Content preview: {doc.get('content', '')[:200]}...")
            

        
    except Exception as e:
        logger.error(f"❌ Error during preprocessing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_preprocessor() 