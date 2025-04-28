from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from src.tools.activity_extractor_tool import extract_activities_from_pdf
from src.tools.activity_match_tool import activity_match_wrapper
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy import create_engine
from langchain_core.runnables.history import RunnableWithMessageHistory
from pathlib import Path

# Database for the agent executor
DB_DIR = Path(__file__).resolve().parent.parent / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DB_DIR / "chat_history.db"
CONNECTION_STRING = f"sqlite:///{DB_FILE.resolve()}"
print("Using SQLite database for chat history:", CONNECTION_STRING)

# Create the agent executor with memory for handling multiple sessions
def create_agent(openai_api_key: str, verbose: bool = True) -> AgentExecutor:
    """
    Initializes the LLM, the specific PDF Activity Extractor Tool, and the Agent Executor.
    """

    print("Initializing LLM (using gpt-4o)...")
    try:
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=openai_api_key,
            model_name="gpt-4o", 
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize ChatOpenAI LLM: {e}")
        raise

    print("Defining the Tools...")
    tools = [
        Tool(
            name="TextbookActivityExtractor",
            func=extract_activities_from_pdf,
            description=(
               "Use this tool ONLY when specifically asked to find, extract, or list classroom activities, experiments, 'let's do', 'let's explore', or similar hands-on sections from a specific PDF textbook file provided via its LOCAL FILE PATH. "
                "Input MUST be the exact file path (relative or absolute) to the source PDF textbook on the local system (e.g., 'path/to/textbook.pdf' or 'C:/docs/science_book.pdf'). The file MUST exist at the given path. "
                "The tool analyzes the PDF content, identifies activities, structures their details (name, concept, materials, description, page number), and saves them to a JSON file. "
                "The tool automatically attempts to process the PDF text directly. If it internally detects that the PDF likely requires Optical Character Recognition (OCR) (e.g., it seems image-based or lacks extractable text), it will automatically ATTEMPT to use an OCR service (Mistral AI) by generating a temporary internal URL. This automatic OCR step requires specific setup and may not always succeed. The user does NOT need to specify whether to use OCR. "
                "The tool returns a string message indicating success (including the full path to the output JSON file, typically saved in the same directory as the input PDF with '_activities.json' appended) or an error message upon failure. "
                "Do NOT use this for processing web URLs directly, general Q&A, simple text summarization, checking inventory, order status, or processing non-PDF files."
            )
        ),
        Tool(
            name="ActivityMatcher", 
            func=activity_match_wrapper,
            description=( 
                "Use ONLY to compare activities between TWO JSON files: a 'Master JSON' file (usually the output from TextbookActivityExtractor) and a 'User JSON' file. Finds activities from the Master JSON that match those in the User JSON and saves ONLY these MATCHING activities to a NEW file (e.g., 'master_activities_matching.json'). IMPORTANT: Returns a success message including the full file path to the new 'matching' JSON file. Input MUST clearly provide BOTH file paths (e.g., '/path/master.json, /path/user.json')."
            )
        )

    ]
    print(f"Tools defined: {[tool.name for tool in tools]}")

    # prompt for the agent using memory
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant for processing textbook activities. You have two tools:\n"
                   "1. TextbookActivityExtractor: Extracts ALL activities from a PDF to a Master JSON file.\n"
                   "2. ActivityMatcher: Compares a Master JSON and a User JSON, saving MATCHING activities to a new file.\n"
                   "Use the chat history to find file paths mentioned in previous turns. If you need two paths for ActivityMatcher and only have one, ask the user for the missing one.\n"
                   "IMPORTANT: When asked about file locations, SEARCH the chat history for messages where tools reported saving files (e.g., 'Results saved to \'/path/to/file.json\''). Report the exact path found in the history if relevant to the user's query. If no specific file path is found in the history related to the query, explain that."
                   ),
        MessagesPlaceholder(variable_name="chat_history"), # <<< Where memory goes
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"), # Where agent thoughts go
    ])

    # Create the agent with the tools and prompt
    try:
        agent = create_openai_functions_agent(llm, tools, prompt)
    except Exception as agent_create_err:
        print(f"ERROR: Failed to create the agent: {agent_create_err}")
        raise
    
    # Create the AgentExecutor
    print("Creating Agent Executor...")
    try:
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=verbose, 
            handle_parsing_errors=True,
            max_iterations=10 # Adjust as needed for your use case
        )
    except Exception as executor_create_err:
        print(f"ERROR: Failed to create the Agent Executor: {executor_create_err}")
        raise

    print("Setting up sqlite database for chat history...")
    # Initialize memory for the agent
    # This is where the chat history will be stored
    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        """Retrieves SQLChatHistory for a given session ID."""
        print(f"Accessing history for session_id: {session_id} using SQLite.") 
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=create_engine(CONNECTION_STRING)
        )
    
    # Create a memory object that uses the message history store
    agent_executor_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        output_messages_key="output",
        history_messages_key="chat_history",
    )
    print("-" * 30)
    print("Agent Executor wrapped successfully using RunnableWithMessageHistory.")
    print("-" * 30)

    return agent_executor_with_history