"""Test Chat mode's requirement clarification ability."""

from modsmith.llm.chat import chat_response

TEST_INPUTS = [
    # Scenario 1: Clear requirement
    "I want to make an apple that heals when eaten",
    # Scenario 2: Vague requirement (should ask follow-up)
    "I want to make something new",
    # Scenario 3: Non-requirement input (should steer back)
    "Nice weather today",
    # Scenario 4: Technical question (should answer briefly and steer back)
    "What is Fabric's registry?",
    # Scenario 5: Out-of-scope requirement
    "I want to make a new mob",
]

for i, user_input in enumerate(TEST_INPUTS, 1):
    print(f"\n{'='*60}")
    print(f"Scenario {i}: {user_input}")
    print('='*60)
    answer = chat_response(user_input)
    print(answer)