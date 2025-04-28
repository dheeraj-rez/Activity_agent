# Activity Agent: Workflow Automation with LangChain

This repository demonstrates the use of LangChain to create a Workflow Automation Agent. The agent is designed to simplify and automate workflows by leveraging the power of advanced language models. Specifically, it implements a specialized conversational AI agent to manage workflows for processing educational activities from PDF textbooks.

## Features

- **Automated Workflows**: Streamlines repetitive tasks and processes.
- **LangChain Integration**: Harnesses LangChain's AgentExecutor and the modern `RunnableWithMessageHistory` pattern for stateful conversations.
- **Persistent Chat History**: Stores chat history in a timestamped SQLite database using a custom `SQLChatMessageHistory` subclass.
- **Powerful Tools**: Equipped with four distinct LangChain Tools:
    1. Extracts all activities from a PDF using PyMuPDF, with OCR fallback via Mistral AI.
    2. Compares extracted activities with a user-provided list and saves matches.
    3. Filters out matched activities for further processing.
    4. Generates new, improved activities from the filtered list using GPT-4o.
- **Highly Customizable**: Adaptable to diverse workflows and scenarios.
- **Readable Codebase**: Clean, modular, and easy-to-understand implementation.

## Requirements

- Python 3.8 or newer
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
        ```bash
        git clone https://github.com/dheeraj-rez/Activity_agent.git
        ```
2. Navigate to the project directory:
        ```bash
        cd Activity_agent
        ```
3. Install the dependencies:
        ```bash
        pip install -r requirements.txt
        ```

## Getting Started

Run the main script to launch the Workflow Automation Agent:
```bash
python main.py
```

Interact with the agent using natural language commands to guide the process from initial PDF extraction to generating refined activity sets.

## License

This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.
