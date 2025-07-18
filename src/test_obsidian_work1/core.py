import os
from openai import OpenAI

def use_llm(prompt: str) -> str:
    """
    This function simulates the usage of a large language model.
    In a real scenario, you would integrate with an LLM API here.
    """
    try:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo", # You can change the model as needed
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {e}"

def generate_text_with_model(topic: str, length: int = 50) -> str:
    """
    Generates text on a given topic using the underlying LLM.
    :param topic: The topic for which to generate text.
    :param length: The desired length of the generated text (approximate).
    :return: Generated text.
    """
    prompt = f"请生成一段关于{topic}的文本，大约{length}字。" # Chinese prompt
    generated_text = use_llm(prompt)
    return generated_text

if __name__ == "__main__":
    test_prompt = "Hello, how are you today?"
    response = use_llm(test_prompt)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")

    another_prompt = "What is the capital of France?"
    response = use_llm(another_prompt)
    print(f"Prompt: {another_prompt}")
    print(f"Response: {response}")

    # Demonstrate the new function
    generated_story = generate_text_with_model("人工智能", 100)
    print(f"\nGenerated text about AI: {generated_story}")

    generated_poem = generate_text_with_model("夏天的雨", 80)
    print(f"\nGenerated text about Summer Rain: {generated_poem}")
