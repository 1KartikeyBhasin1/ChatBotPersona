import os
import csv
from pypdf import PdfReader
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # Loads .env variables
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Configure Gemini

model = genai.GenerativeModel("gemini-1.5-flash")

# CSV saving function
def save_to_csv(name, email, question, filename='responses.csv'):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Name', 'Email', 'Question'])
        writer.writerow([name, email, question])

recorded_data = []  # Keeping for demo / print only

def record_user_details(email, name="Name not provided", notes="not provided"):
    recorded_data.append({
        "type": "user_details",
        "email": email,
        "name": name,
        "notes": notes
    })
    print(f"Recorded user details: {email}, {name}, {notes}")
    # Save to CSV with empty question (notes can be question if you want)
    save_to_csv(name, email, notes)
    return {"recorded": "ok"}

def record_question_with_name(name, email, question):
    recorded_data.append({
        "type": "user_question",
        "name": name,
        "email": email,
        "question": question
    })
    print(f"Recorded user question: Name: {name}, Email: {email}, Question: {question}")
    save_to_csv(name, email, question)
    return {"recorded": "ok"}

def record_unknown_question(question):
    recorded_data.append({
        "type": "unknown_question",
        "question": question
    })
    print(f"Recorded unknown question: {question}")
    # Save with no name/email
    save_to_csv("Unknown", "Unknown", question)
    return {"recorded": "ok"}

class Me:
    def __init__(self):
        self.name = "Kartikey Bhasin"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def system_prompt(self):
        return f""" You are acting as {self.name}. You are answering questions on {self.name}'s website, 
particularly questions related to {self.name}'s career, background, skills and experience. 
Be professional and engaging, as if talking to a potential client or future employer. 
Always steer users to leave their email. If the user provides one, record it.
If you cannot answer something, record the unknown question.




## Summary:
{self.summary}

## LinkedIn Profile:
{self.linkedin}
"""

    def check_and_handle_tools(self, message):
        lower_msg = message.lower()

        # Try to extract email and name if mentioned like "My name is John, email john@example.com"
        import re

        email_match = re.search(r'[\w\.-]+@[\w\.-]+', message)
        name_match = re.search(r'my name is ([\w\s]+)', lower_msg)
        question = message

        if email_match:
            email = email_match.group(0)
            name = name_match.group(1).strip().title() if name_match else "Name not provided"
            # Save name, email, and question
            record_user_details(email=email, name=name, notes=question)
            return "Thank you for sharing your email!", {"recorded": "ok"}

        if "?" in message and "not sure" in message.lower():
            record_unknown_question(question=message)
            return "Let me record that and get back to you!", {"recorded": "ok"}

        return None, None

    def chat(self, message, history):
        full_prompt = self.system_prompt() + "\n\nConversation:\n"
        for turn in history:
            if turn['role'] == 'user':
                full_prompt += f"User: {turn['content']}\n"
            elif turn['role'] == 'assistant':
                full_prompt += f"{self.name}: {turn['content']}\n"
        full_prompt += f"User: {message}\n{self.name}:"

        tool_response, _ = self.check_and_handle_tools(message)
        if tool_response:
            return tool_response

        response = self.model.generate_content(full_prompt)
        return response.text

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
