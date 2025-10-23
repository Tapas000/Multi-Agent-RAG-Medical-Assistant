"""
Flask Backend for Medical AI Chatbot - Production Ready
Optimized for Render deployment
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your graph
from src.langgraph.graph import build_graph

# Initialize Flask app with static files
app = Flask(__name__, static_folder='static', static_url_path='')

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Change to specific domain in production
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Get port from environment (Render provides this)
PORT = int(os.environ.get('PORT', 8000))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'chat_history.db')

def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                message TEXT NOT NULL,
                is_user BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id 
            ON messages(chat_id)
        ''')

        conn.commit()
        conn.close()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init error: {e}")

# Initialize on startup
print("🔄 Initializing...")
init_db()

print("🔄 Building LangGraph...")
try:
    graph = build_graph()
    print("✅ Graph ready")
except Exception as e:
    print(f"❌ Graph error: {e}")
    graph = None

# Serve frontend
@app.route('/')
def index():
    """Serve frontend index.html"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, etc)"""
    try:
        return send_from_directory('static', path)
    except:
        return send_from_directory('static', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Medical AI API is running",
        "graph_loaded": graph is not None,
        "port": PORT
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        chat_id = data.get('chat_id')

        if not query:
            return jsonify({"error": "Query is required"}), 400

        if not graph:
            return jsonify({"error": "AI model not initialized"}), 500

        print(f"📨 Query: {query[:50]}...")

        # Run through graph
        initial_state = {
            "query": query,
            "tool": "",
            "results": [],
            "metadata": {},
            "final_answer": ""
        }

        result = graph.invoke(initial_state)
        answer = result.get("final_answer", "Sorry, I couldn't generate a response.")

        print(f"✅ Response generated ({len(answer)} chars)")

        # Save to database
        if chat_id:
            save_message(chat_id, query, True)
            save_message(chat_id, answer, False)
            update_chat_title(chat_id, query)

        return jsonify({
            "answer": answer,
            "query": query,
            "tool_used": result.get("tool", "unknown"),
            "chat_id": chat_id
        })

    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats', methods=['GET'])
def get_chats():
    """Get all chat sessions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, title, created_at, updated_at 
            FROM chats 
            ORDER BY updated_at DESC
            LIMIT 100
        ''')

        chats = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({"chats": chats})

    except Exception as e:
        print(f"❌ Get chats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get specific chat with messages"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM chats WHERE id = ?', (chat_id,))
        chat = cursor.fetchone()

        if not chat:
            conn.close()
            return jsonify({"error": "Chat not found"}), 404

        cursor.execute('''
            SELECT message, is_user, created_at 
            FROM messages 
            WHERE chat_id = ? 
            ORDER BY created_at ASC
        ''', (chat_id,))

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            "chat": dict(chat),
            "messages": messages
        })

    except Exception as e:
        print(f"❌ Get chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats', methods=['POST'])
def create_chat():
    """Create new chat session"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        title = data.get('title', 'New Chat')

        if not chat_id:
            return jsonify({"error": "chat_id required"}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM chats WHERE id = ?', (chat_id,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"message": "Chat exists", "chat_id": chat_id})

        cursor.execute('INSERT INTO chats (id, title) VALUES (?, ?)', (chat_id, title))
        conn.commit()
        conn.close()

        return jsonify({"message": "Chat created", "chat_id": chat_id})

    except Exception as e:
        print(f"❌ Create chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete chat session"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
        cursor.execute('DELETE FROM chats WHERE id = ?', (chat_id,))

        conn.commit()
        conn.close()

        return jsonify({"message": "Chat deleted"})

    except Exception as e:
        print(f"❌ Delete chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chats/clear', methods=['DELETE'])
def clear_all_chats():
    """Clear all chat history"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM messages')
        cursor.execute('DELETE FROM chats')

        conn.commit()
        conn.close()

        return jsonify({"message": "All chats cleared"})

    except Exception as e:
        print(f"❌ Clear chats error: {e}")
        return jsonify({"error": str(e)}), 500

def save_message(chat_id, message, is_user):
    """Save message to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM chats WHERE id = ?', (chat_id,))
        if not cursor.fetchone():
            title = message[:50] + ('...' if len(message) > 50 else '')
            cursor.execute('INSERT INTO chats (id, title) VALUES (?, ?)', (chat_id, title))

        cursor.execute('UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (chat_id,))
        cursor.execute('INSERT INTO messages (chat_id, message, is_user) VALUES (?, ?, ?)',
                      (chat_id, message, is_user))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Save message error: {e}")

def update_chat_title(chat_id, first_message):
    """Update chat title from first message"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM messages WHERE chat_id = ? AND is_user = 1', (chat_id,))
        count = cursor.fetchone()[0]

        if count == 1:
            title = first_message[:50] + ('...' if len(first_message) > 50 else '')
            cursor.execute('UPDATE chats SET title = ? WHERE id = ?', (title, chat_id))
            conn.commit()

        conn.close()
    except Exception as e:
        print(f"❌ Update title error: {e}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 Medical AI Chatbot")
    print("="*60)
    print(f"🌐 Server: http://0.0.0.0:{PORT}")
    print("="*60 + "\n")

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,  # Set False for production
        threaded=True
    )