from langchain_ollama import ChatOllama

print("Testing Ollama integration...")

llm = ChatOllama(model="mistral", temperature=0.1)
response = llm.invoke("Say 'Ollama is working!' in exactly those words.")

print(f"Response: {response.content}")
print("✅ Ollama integration successful!")
