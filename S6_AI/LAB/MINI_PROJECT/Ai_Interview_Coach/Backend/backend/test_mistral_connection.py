"""
Test Your Mistral Model Connection
Run this FIRST to make sure your LM Studio is working
"""

from openai import OpenAI
import sys

def test_mistral():
    """Test if Mistral model is running and responding"""
    
    print("🔍 Testing Mistral Connection...")
    print("=" * 50)
    
    try:
        # Connect to your LM Studio
        client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="not-needed"  # LM Studio doesn't need real API key
        )
        
        print("✅ Connected to LM Studio")
        
        # Test 1: Simple hello
        print("\n📝 Test 1: Asking Mistral to say hello...")
        response = client.chat.completions.create(
            model="mistral-7b-instruct-v0.2",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=50
        )
        
        answer = response.choices[0].message.content
        print(f"   Mistral replied: {answer}")
        
        # Test 2: Generate interview question
        print("\n📝 Test 2: Asking Mistral to generate interview question...")
        response = client.chat.completions.create(
            model="mistral-7b-instruct-v0.2",
            messages=[{
                "role": "user", 
                "content": "Generate ONE interview question for a Frontend Developer at Intermediate level."
            }],
            max_tokens=100
        )
        
        question = response.choices[0].message.content
        print(f"   Question generated: {question}")
        
        # Test 3: Analyze answer
        print("\n📝 Test 3: Asking Mistral to analyze an answer...")
        response = client.chat.completions.create(
            model="mistral-7b-instruct-v0.2",
            messages=[{
                "role": "user",
                "content": """Analyze this interview answer and give a score from 1-10:
                
Question: Explain React hooks
Answer: React hooks like useState and useEffect allow functional components to use state and lifecycle features.

Give score and brief feedback."""
            }],
            max_tokens=150
        )
        
        feedback = response.choices[0].message.content
        print(f"   Feedback: {feedback}")
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("✅ Your Mistral model is working perfectly!")
        print("✅ You can now run: python app_ULTIMATE.py")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ ERROR: Cannot connect to Mistral")
        print(f"   Error: {str(e)}")
        print("\n💡 SOLUTION:")
        print("   1. Open LM Studio")
        print("   2. Load 'mistral-7b-instruct-v0.2' model")
        print("   3. Click 'Start Server' (should show port 1234)")
        print("   4. Run this test again")
        print("=" * 50)
        
        return False

if __name__ == '__main__':
    success = test_mistral()
    sys.exit(0 if success else 1)
