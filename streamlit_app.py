# streamlit_app.py
import streamlit as st
import os
import tempfile
from pathlib import Path
import time
import re # Import regular expressions for parsing file paths

# Assuming your agent setup and config loading are correct
try:
    from src.agent.agent_setup import create_agent
    # We assume create_agent or its dependencies will handle loading the key via os.getenv
except ImportError as e:
    st.error(f"Failed to import necessary modules: {e}")
    st.info("Please ensure 'src/agent/agent_setup.py' exists and is correct.")
    st.stop()

# --- Page Configuration (Full Width) ---
st.set_page_config(
    page_title="Conversational PDF Extractor",
    page_icon="💬",
    layout="wide"
)

# --- State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if 'temp_pdf_path' not in st.session_state:
    st.session_state['temp_pdf_path'] = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state['uploaded_file_name'] = None

# --- Helper Function for Temp File Cleanup ---
def cleanup_temp_file():
    path_to_delete = st.session_state.get('temp_pdf_path')
    if path_to_delete and os.path.exists(path_to_delete):
        # Also try to delete the expected output JSON in the same directory
        output_json_path = Path(path_to_delete).with_suffix(".json") # Assumes _activities.json convention isn't strictly followed by tool
        output_json_path_alt = Path(path_to_delete).with_name(Path(path_to_delete).stem + "_activities.json")

        files_to_delete = [path_to_delete, output_json_path, output_json_path_alt]
        for file_path in files_to_delete:
             if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Cleaned up temp file: {file_path}")
                except OSError as e:
                    print(f"Error deleting temp file {file_path}: {e}")

    # Always reset state variables after attempting cleanup
    st.session_state['temp_pdf_path'] = None
    st.session_state['uploaded_file_name'] = None


# --- Sidebar for File Upload ONLY ---
with st.sidebar:
    st.title("📄 PDF Upload")
    st.markdown("Optionally upload a PDF if your query involves processing one.")

    uploaded_file = st.file_uploader(
        "Upload PDF here:",
        type=["pdf"],
        help="Upload a PDF file. Then, ask the agent about it in the chat.",
        on_change=cleanup_temp_file
    )

    # Process uploaded file
    if uploaded_file is not None:
        if st.session_state['temp_pdf_path'] is None or Path(st.session_state['temp_pdf_path']).name != uploaded_file.name:
            cleanup_temp_file()
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
                    tf.write(uploaded_file.getvalue())
                    st.session_state['temp_pdf_path'] = tf.name
                    st.session_state['uploaded_file_name'] = uploaded_file.name
                print(f"Created temp file: {st.session_state['temp_pdf_path']} for {st.session_state['uploaded_file_name']}")
                st.success(f"'{st.session_state['uploaded_file_name']}' ready.", icon="✅")
            except Exception as e:
                st.error(f"Error creating temporary file: {e}")
                cleanup_temp_file()
        else:
            st.success(f"'{st.session_state['uploaded_file_name']}' ready.", icon="✅")
    elif st.session_state.get('temp_pdf_path'):
        cleanup_temp_file()

    # Display currently active file info
    if st.session_state.get('temp_pdf_path') and st.session_state.get('uploaded_file_name'):
        st.info(f"**Active PDF:** `{st.session_state['uploaded_file_name']}`")
        # st.caption(f"Temp Path: `{st.session_state['temp_pdf_path']}`") # Optional: Show temp path


# --- Main Chat Interface ---
st.title("💬 Conversational PDF Activity Extractor")
st.markdown("Chat with the agent below. Use the sidebar to upload a PDF first if needed.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Display logs if they exist for this assistant message
        if message["role"] == "assistant" and "logs" in message and message["logs"]:
            with st.expander("Show Agent Steps"):
                st.text(message["logs"])
        # Display download button if it exists for this assistant message
        if message["role"] == "assistant" and "download_info" in message and message["download_info"]:
            info = message["download_info"]
            try:
                with open(info["path"], "rb") as fp:
                    st.download_button(
                        label=f"Download '{info['name']}'",
                        data=fp,
                        file_name=info["name"],
                        mime="application/json" # Adjust mime type if needed
                    )
            except Exception as e:
                st.error(f"Error preparing download for {info['name']}: {e}")


# Accept user input
if prompt := st.chat_input("Ask the agent..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Get API Key (Essential) ---
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        error_msg = "OpenAI API key not found in environment variables. Please set OPENAI_API_KEY."
        st.error(error_msg, icon="🔑")
        st.session_state.messages.append({"role": "assistant", "content": error_msg, "logs": None, "download_info": None})
    else:
        # --- Prepare prompt for Agent ---
        full_prompt_for_agent = prompt
        temp_pdf_path = st.session_state.get('temp_pdf_path')
        uploaded_file_name = st.session_state.get('uploaded_file_name')

        if temp_pdf_path and os.path.exists(temp_pdf_path) and uploaded_file_name:
            formatted_path = Path(temp_pdf_path).as_posix()
            file_context = f"\n\n[System Note: A PDF file named '{uploaded_file_name}' is available for processing at path: {formatted_path}]"
            full_prompt_for_agent += file_context
            print(f"Agent Prompt includes file context. Path: {formatted_path}")
        else:
            print("Agent Prompt does not include file context.")

        print(f"Full prompt sent to agent:\n---\n{full_prompt_for_agent}\n---")

        # Display thinking message
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking... 🧠")

            # --- Call the Agent ---
            agent_response_text = None
            agent_error = None
            intermediate_steps_log = ""
            download_button_info = None

            try:
                # Create the agent, enable return_intermediate_steps
                # NOTE: verbose=True still prints to console, not captured here directly
                agent_executor = create_agent(
                    openai_api_key,
                    verbose=False, # Set verbose=False if console logs are too much
                    # return_intermediate_steps=True # This argument might not exist directly here
                                                      # depends on how create_agent is implemented
                )
                # Check if agent_executor supports configuring return_intermediate_steps
                # It's usually set on AgentExecutor directly:
                if hasattr(agent_executor, 'return_intermediate_steps'):
                    agent_executor.return_intermediate_steps = True
                else:
                    print("Warning: AgentExecutor might not support 'return_intermediate_steps'. Logs might be unavailable.")


                # Run the agent
                response_dict = agent_executor.invoke({"input": full_prompt_for_agent})
                agent_response_text = response_dict.get('output', 'Agent did not produce standard output.')

                # --- Process Intermediate Steps for Logs ---
                if 'intermediate_steps' in response_dict:
                    steps_text = []
                    for i, (action, observation) in enumerate(response_dict['intermediate_steps']):
                        steps_text.append(f"Step {i+1}:")
                        steps_text.append(f"  Action Tool: {action.tool}")
                        steps_text.append(f"  Action Input: {action.tool_input}")
                        # steps_text.append(f"  Log: {action.log.strip()}") # May contain more detail
                        steps_text.append(f"  Observation: {observation}")
                        steps_text.append("-" * 30)
                    intermediate_steps_log = "\n".join(steps_text)
                else:
                    intermediate_steps_log = "No intermediate steps were returned by the agent executor."


                # --- Check for Downloadable File Path in Response ---
                # Try to find a file path (adjust regex if needed)
                # Looks for "saved to '<path>.json'" or similar, capturing the path
                match = re.search(r"saved to ['\"]?([^'\"]+\.json)['\"]?", agent_response_text, re.IGNORECASE)
                if match:
                    potential_path_str = match.group(1)
                    potential_path = Path(potential_path_str)
                    temp_dir = Path(st.session_state['temp_pdf_path']).parent if st.session_state.get('temp_pdf_path') else None

                    # Security/Sanity Check: Ensure it exists and is in the expected temp directory
                    if temp_dir and potential_path.exists() and potential_path.parent == temp_dir:
                        print(f"Found valid output file path: {potential_path}")
                        download_button_info = {
                            "path": str(potential_path),
                            "name": potential_path.name
                        }
                    else:
                         print(f"Found path '{potential_path_str}' in response, but it's invalid or not in temp dir.")


            except Exception as e:
                agent_error = f"An error occurred during agent execution: {e}"
                import traceback
                traceback.print_exc()

            # --- Update UI and History ---
            final_content = agent_error if agent_error else agent_response_text
            message_placeholder.markdown(final_content if final_content else "Agent finished.") # Update placeholder

            # Display download button if available WITHIN the message block
            if download_button_info:
                 try:
                    with open(download_button_info["path"], "rb") as fp:
                        st.download_button(
                            label=f"Download '{download_button_info['name']}'",
                            data=fp,
                            file_name=download_button_info["name"],
                            mime="application/json"
                        )
                 except Exception as e:
                    st.error(f"Error preparing download for {download_button_info['name']}: {e}")

            # Display logs in expander if available WITHIN the message block
            if intermediate_steps_log:
                with st.expander("Show Agent Steps"):
                    st.text(intermediate_steps_log)

            # Add the complete message object to history (including logs/download info for redisplay)
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_content if final_content else "Agent finished.",
                "logs": intermediate_steps_log,
                "download_info": download_button_info
            })