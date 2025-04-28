from flask import Flask, request, jsonify
from src.agent.agent_setup import create_agent
import os
from dotenv import load_dotenv
import logging

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Agent executor setup
agent_executor = None

try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logging.error("OPENAI_API_KEY not found in environment variables.")

    else:
        logging.info("Creating agent executor...")
        agent_executor = create_agent(openai_api_key, verbose=True)
        logging.info("Agent executor created successfully.")
except Exception as e:
    logging.error(f"Error creating agent executor: {e}")
    raise

#  API endpoint to handle requests
@app.route('/chat', methods=['POST'])
def handle_chat():
    """Handles incoming chat requests."""
    if agent_executor is None:
        logging.error("Chat request received but agent is not initialized.")
        return jsonify({"error": "Agent service is currently unavailable."}), 503 #

    # get JSON payload from request
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    user_input = data.get('input')
    session_id = data.get('session_id') 

    if not user_input or not session_id:
        missing = []
        if not user_input: missing.append("'input'")
        if not session_id: missing.append("'session_id'")
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    logging.info(f"Received request for session_id: {session_id}")

    agent_input_dict = {"input": user_input}
    agent_config = {"configurable": {"session_id": session_id}}

    # Invoke the agent with the input data and session ID
    try:
        logging.info(f"Invoking agent for session_id: {session_id}...")
        response = agent_executor.invoke(agent_input_dict, config=agent_config)
        logging.info(f"Agent invocation complete for session_id: {session_id}.")

        output_data = {
            "session_id": session_id,
            "output": response.get('output', "Agent executed but produced no standard output.") 
        }
        return jsonify(output_data), 200

    except Exception as e:
        logging.exception(f"ERROR during agent execution for session {session_id}: {e}") 
        return jsonify({"error": "An internal error occurred processing the request."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Run the Flask app
    