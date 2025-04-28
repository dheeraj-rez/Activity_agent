import sys
from src.agent.agent_setup import create_agent
from src.config import load_api_key
import uuid

def run_agent_query(agent_executor, query: str):
    """Runs a query through the agent executor and prints the result."""
    print(f"\n> You: {query}")
    try:
        response = agent_executor.invoke({"input": query}, config={"configurable": {"session_id": str(uuid.uuid4())}})
        print(f"< Agent: {response['output']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Loading configuration and initializing agent...")
    try:
        # Load the API key and create the agent
        api_key = load_api_key()
        agent_executor = create_agent(openai_api_key=api_key, verbose=True)

        print("Agent created successfully.")

        # Generate a unique session ID for the agent
        session_id = str(uuid.uuid4())
        print("-" * 30)
        print(f"Session ID: {session_id}")
        print("This session ID is unique to this run and can be used to track the conversation history.")
        print("You can use this ID to refer to this session in future queries.")
        print("-" * 30)

        # Prompt the user for input
        print("Agent initialized.")
        print("Enter your query below (type 'exit' or 'quit' to stop):")

        while True:
            user_query = input("> You: ")
            if user_query.lower() in ["exit", "quit"]:
                break
            if not user_query:
                continue

            print("< Agent is thinking...")

            try:
                response = agent_executor.invoke(
                    {"input": user_query},
                    config={'configurable': {'session_id': session_id}},
                    )
                print(f"< Agent: {response['output']}")
            except Exception as e:
                print(f"An error occurred during agent execution: {e}")

    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1) 
    except Exception as e:
        print(f"An unexpected error occurred during setup: {e}")
        sys.exit(1)

    print("\nExiting application.")