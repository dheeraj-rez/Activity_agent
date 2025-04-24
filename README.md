# 📚 Textbook Activity Extractor Agent

This project implements a specialised AI agent using the Langchain framework, designed to extract structured information about classroom activities from textbook PDF files. It leverages Large Language Models (LLMs) like GPT-4o and text extraction libraries (PyMuPDF, potentially Mistral AI OCR) to analyze documents and generate useful output.

## ✨ Features

*   **Langchain Agent:** Built using `AgentExecutor` for managing interactions and tool usage.
*   **Specialized Tool:** Features a single, powerful `TextbookActivityExtractor` tool focused solely on processing PDF textbooks.
*   **Activity Extraction:** Identifies sections like "Activity", "Let's Explore", "Experiment", etc., within the PDF text.
*   **Structured Output:** Extracts key details for each activity (name, concept, materials, description, page number) and saves them into a well-formatted JSON file.
*   **Automatic OCR Detection:** Internally attempts to determine if a PDF requires OCR (e.g., image-based) using a `need_ocr` check.
*   **Conditional OCR Processing:** If OCR is deemed necessary, it attempts to process the PDF using Mistral AI's OCR capabilities (requires specific setup and a MISTRAL_API_KEY).
*   **Local File Processing:** Primarily designed to work with PDF files accessible via local file paths.
*   **Configurable:** Uses environment variables for API keys.

## 📂 Project Structure
Use code with caution.
Markdown
your_project_directory/
├── .env # Stores API keys (DO NOT COMMIT TO GIT)
├── main.py # Main script to run the agent
├── requirements.txt # Project dependencies
└── src/
├── agent/
│ └── agent_setup.py # Initializes LLM, Tool, and AgentExecutor
├── config.py # Utility for loading configuration (optional)
└── tools/
└── activity_extractor_tool.py # Contains the complex activity extractor logic
## ⚙️ Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd your_project_directory
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Make sure you have a `requirements.txt` file listing all necessary libraries (see Dependencies section below).
    ```bash
    pip install -r requirements.txt
    ```

## 🔑 Configuration

1.  **Create `.env` file:** In the root directory of the project (`your_project_directory/`), create a file named `.env`.
2.  **Add API Keys:** Add your API keys to the `.env` file:
    ```plaintext
    # .env
    OPENAI_API_KEY="your_openai_api_key_here"
    MISTRAL_API_KEY="your_mistral_api_key_here" # Required for the automatic OCR fallback
    ```
3.  **Security:** Ensure the `.env` file is listed in your `.gitignore` file to prevent accidentally committing sensitive keys.

## ▶️ Usage

1.  **Run the Agent:** Execute the main script from the root directory:
    ```bash
    python main.py
    ```
2.  **Interact:** The script will load the configuration, initialize the agent, and prompt you for input. Ask the agent to process a PDF file using its local path.

    **Example Prompts:**
    *   `"Please extract the activities from the textbook located at C:/Users/MyUser/Documents/Science_Grade7.pdf"`
    *   `"Can you find the experiments listed in /data/textbooks/physics_book.pdf?"`
    *   `"Extract activities from assets/CLS_7.pdf"`

    The agent will use the `TextbookActivityExtractor` tool with the provided path.

## 🛠️ Tool Details: `TextbookActivityExtractor`

*   **Purpose:** Solely designed to find and extract structured details about classroom activities from PDF textbooks.
*   **Input:** Requires the **exact local file path** (relative or absolute) to the PDF file. The file must exist on the system where the agent is running.
*   **Processing:**
    1.  Analyzes the input PDF path.
    2.  **Attempts direct text extraction** using PyMuPDF (suitable for text-based PDFs).
    3.  **Automatic OCR Check:** Internally runs a check (`need_ocr`) to determine if the PDF likely requires OCR (e.g., low text yield, image-based).
    4.  **Conditional OCR Attempt:** If OCR is deemed necessary, it *attempts* to use Mistral AI OCR. This typically involves internally generating a temporary signed URL for the local file (requires appropriate cloud storage setup and permissions configured within the `get_pdf_signed_url` function, which is *not* part of the standard libraries) and requires a valid `MISTRAL_API_KEY`. This step might fail if the setup is incomplete or the service is unavailable.
    5.  Uses OpenAI's GPT-4o model to analyze extracted text chunks, identify relevant activity keywords ("Activity", "Let's do", etc.), and parse out structured details.
    6.  May utilize FAISS for vector indexing (though the current search logic might bypass direct vector *search*).
*   **Output:**
    *   Creates a JSON file containing the structured list of extracted activities. This file is typically saved in the **same directory** as the input PDF, with `_activities.json` appended to the original filename (e.g., `Science_Grade7_activities.json`).
    *   Returns a string message to the agent indicating success (including the full path to the JSON file) or detailing any errors encountered during the process.

## 🚀 Future Improvements

*   Implement direct file upload handling for Mistral OCR instead of relying on signed URLs.
*   Optimize the `search_activity` function – either fully utilize the FAISS index for vector search or remove the embedding/FAISS steps if only keyword search is desired.
*   Add support for different LLMs or embedding models.
*   Improve error handling and reporting granularity.
*   Develop a simple UI (e.g., using Streamlit) for easier interaction.
*   Add caching mechanisms for embeddings or GPT responses.

## 📄 License
MIT License – © 2025 Dheeraj / Rezolut Infotech
