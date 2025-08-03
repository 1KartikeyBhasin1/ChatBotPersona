from flask import Flask, request, jsonify
from mychatbot import Me
from flask_cors import CORS
from flask import render_template
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your frontend
me = Me()

@app.route('/')
def home():
    return render_template('index.html')  # this will load index.html from /templates
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    history = data.get('history', [])
    # Convert history to the format expected by me.chat
    formatted_history = []
    for turn in history:
        if turn.get('role') and turn.get('content'):
            formatted_history.append({'role': turn['role'], 'content': turn['content']})
    response = me.chat(message, formatted_history)
    return jsonify({'reply': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
