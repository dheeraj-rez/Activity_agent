import os
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain import hub 
from src.tools.activity_extractor_tool import extract_activities_from_pdf

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

    print("Defining the TextbookActivityExtractor Tool...")
    tools = [
        Tool(
            name="TextbookActivityExtractor",
            func=extract_activities_from_pdf,
            description=(
                "Use this tool ONLY when specifically asked to find, extract, or list classroom activities, experiments, 'let's do', 'let's explore', or similar hands-on sections from a textbook PDF file. "
                "It analyzes the PDF content (primarily text-based) to identify these activities, structures their details (name, concept, materials, description, page number), and saves them to a JSON file. "
                "Input MUST be the exact file path (relative or absolute) to the source PDF textbook (e.g., 'path/to/textbook.pdf' or 'C:/docs/science_book.pdf'). "
                "The tool returns a string message indicating success (including the full path to the output JSON file, which is saved in the same directory as the PDF) or an error message upon failure. "
                "If the user provides a public document URL AND explicitly requests OCR processing (for image-heavy PDFs), mention that the tool *can* attempt this method via the URL, but the primary input method is the file path. "
                "Do NOT use this for any other purpose like general Q&A, simple text summarization, checking inventory, order status, or processing non-PDF files."
            )
        )
    ]

    try:
        # This prompt helps the agent understand how to use tools and function calling
        prompt = hub.pull("hwchase17/openai-functions-agent")
    except Exception as hub_err:
        print(f"ERROR: Failed to pull prompt from Langchain Hub: {hub_err}")
        print("Please ensure network connectivity and that the prompt identifier is correct.")
        raise RuntimeError("Could not load agent prompt.") from hub_err

    try:
        agent = create_openai_functions_agent(llm, tools, prompt)
    except Exception as agent_create_err:
        print(f"ERROR: Failed to create the agent: {agent_create_err}")
        raise

    print("Creating Agent Executor...")
    try:
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=verbose, 
            handle_parsing_errors=True,
            max_iterations=10,
        )
    except Exception as executor_create_err:
        print(f"ERROR: Failed to create the Agent Executor: {executor_create_err}")
        raise

    print("-" * 30)
    print("Agent Executor created successfully.")
    print("-" * 30)
    return agent_executor