
import gradio as gr
import logging
import requests
import json
import os

# Configure logging to display INFO level messages
logging.basicConfig(level=logging.INFO)

class ContextualQA:
    def __init__(self, api_url, api_token, model="your-model-name"):
        logging.info("Initializing ContextualQA class.")
        self.api_url = api_url
        self.api_token = api_token
        self.model = model
        self.context = ""

    def load_text_from_file(self, filename):
        logging.info(f"Loading text from file: {filename}")
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                logging.info("File content loaded successfully.")
                return content
        except FileNotFoundError:
            logging.error(f"File {filename} not found.")
            return ""
        except UnicodeDecodeError as e:
            logging.error(f"Unicode decoding error in {filename}: {e}")
            return ""

    def load_context(self):
        logging.info("Loading context.")
        self.context = self.load_text_from_file('context.txt')

    def ask_question(self, question, temperature=0.01, max_tokens=1024, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
        logging.info(f"Asking question to the model: {question}")
        if not question.strip():
            return "Please enter a question."

        prompt = f"""
        SYSTEM INSTRUCTIONS: You are PPC-Agent, a sophisticated AI chatbot designed to answer Pro Power Clean employment and policy questions for employees. You are only allowed to discuss topics that are directly related to working at Pro Power Clean, and you must refuse to answer questions about any other unrelated topic. Your answer must NOT contain: Extra or irrelevant information, (((PLEASE DO NOT GIVE AN ANSWER MORE THAN ONCE, ALSO PLEASE DO NOT INCLUDE OFF-TOPIC INFORMATION IN YOUR RESPONSE.))) QUESTION: Please answer the following question using only this context information only, if you can't find the answer to the question in the context information, please simply reply 'I'm sorry I can't answer this question. Please try again.'. USING THE FOLLOWING CONTEXT: {self.context} PLEASE ANSWER THE QUESTION: {question}?
        PPC-AI: (Concise and accurate answer to the question using the context data)</s> 
        """
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        response = requests.post(self.api_url, headers=headers, json=data, timeout=120)

        if response.status_code == 200:
            response_body = response.json()
            if "error" in response_body:
                logging.error(f"API Error: {response_body['error']}")
                return "I am unable to answer this question due to an error."
            answer = response_body.get('choices', [{}])[0].get('text', '').strip()
            return answer
        else:
            logging.error(f"Error in API call: {response.status_code} - {response.text}")
            return "I am unable to answer this question due to an error."

# Instantiate the class with the secrets

api_url = "https://ef6odmqhwebmh4-5000.proxy.runpod.net/v1/completions"  # Replace with your actual API URL
api_token = "2087611377"  # Replace with your actual API token
contextual_qa = ContextualQA(api_url, api_token)

# Load context from files
contextual_qa.load_context()

# Load bad words from file
bad_words_file = 'bad_words.txt'
try:
    with open(bad_words_file, 'r', encoding='utf-8') as file:
        bad_words = file.read().splitlines()
except FileNotFoundError:
    logging.error(f"Bad words file not found: {bad_words_file}")
    bad_words = []

# Define the chat function
def chat_function(username, message, chat_history):
    if not username.strip():
        return [("Error: Please enter a username.", "")]
    if not message.strip():
        return chat_history
    response = contextual_qa.ask_question(message)
    chat_history.append((f"{username}: " + message, "AI: " + response))
    return chat_history  # Return the updated chat history

# Function to handle flagging
def flag_response(flag_data, chat_history):
    # Save the flag_data to a JSON file or handle it as needed
    with open("flagged_data.json", "a") as f:
        json.dump(flag_data, f)
        f.write("\n")
    return chat_history

# Function to check for bad words and auto-flag
def check_for_bad_words(message):
    for bad_word in bad_words:
        if bad_word.lower() in message.lower():
            return True
    return False

# Create Gradio interface using Blocks
with gr.Blocks() as demo:
    logo_path = "PPC_LOGO-SM.png"  # Replace with the path to your logo image
    if os.path.exists(logo_path):
        gr.Image(value=logo_path, width=300)  # Adjust width as needed
    gr.Markdown("### PPC-AI | Human Resources & Policy Chatbot")
    username = gr.Textbox(label="Enter your username", placeholder="Username")
    chat_history = gr.State([])  # Initialize the chat history as an empty list
    chatbot = gr.Chatbot()  # Create the Chatbot component
    with gr.Row():
        msg = gr.Textbox(placeholder="Ask a question...", label="Your Question")
        submit_button = gr.Button("Submit")
    submit_button.click(chat_function, inputs=[username, msg, chat_history], outputs=chatbot)

    # Add a flag button to manually flag responses
    flag_data = gr.State({})  # State to hold data to be flagged
    flag_button = gr.Button("Flag Response")
    flag_button.click(flag_response, inputs=[flag_data, chat_history], outputs=chatbot)

    # Update flag_data state when a new message is submitted
    def update_flag_data(username, message, chat_history):
        if not username.strip():
            return {"error": "Please enter a username"}, chat_history
        if not message.strip():
            return {}, chat_history
        response = contextual_qa.ask_question(message)
        # Check for bad words and auto-flag if necessary
        if check_for_bad_words(message):
            flag_data = {"username": username, "message": message, "response": response}
            flag_response(flag_data, chat_history)
        return {"username": username, "message": message, "response": response}, chat_history

    msg.change(update_flag_data, inputs=[username, msg, chat_history], outputs=[flag_data, chat_history])
    
    # Optionally, you can add a button to clear the chat history if needed
    clear_button = gr.Button("Clear Chat")
    def clear_chat():
        return []  # Return an empty list to clear the chat history
    clear_button.click(clear_chat, inputs=[], outputs=chatbot)

    # Add a block of text under the "Clear Chat" button
    gr.Markdown("""
    
    WARNING | IMPORTANT NOTICE:
This is a BETA test project built on artificial intelligence which is a new and emerging technology. AI can at times give incorrect, incoherent, or even offensive answers. The information received from this AI assistant is to be used for educational purposes only, please be sure to verify any critical information with a human member of the supervisory or management team before implementation.

Rules of Acceptable Use:
1. Your real first and last names must be used in the username field.
2. No inappropriate conversations with the AI, if you wouldn't say it to the president, don't say it to the AI.
3. Keep it business. The AI is only for work related questions and conversations.
4. Verify information with a human first if questionable.
5. Please hit the Flag button to report any inaccurate or offensive responses from the AI.
\n>
TIPS:\n>
1. Give lots of background context, see example:\n>
Example #1\n>
IDEAL: I am a new route janitor and would like to know how bonuses incentives are paid?\n>
NOT-IDEAL: How do we get paid?\n>
\n>
\n>
2. Be very clear in what you want to know, see example: \n>
Example #2 \n>
IDEAL: I was wondering if it is ok for me to pick up beer on my way back to the shop. I don't plan to drink it until I am off the premises and off the clock. \n>
NOT-IDEAL: Can I pick up beer while working? \n>
(((The answer to both is still NO :-) \n>
\n>
\n>
3. BE PATIENT!\n>
Answers can take 5 seconds all the way up to a minute depending on tablet reception, network traffic, and complexity of question. The average response is probably around 20 seconds. \n>

    
    """
    )

# Launch the Gradio app
demo.launch(server_name='0.0.0.0', server_port=7869)
