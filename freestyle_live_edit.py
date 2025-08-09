#!/usr/bin/env python3
"""
Flask server for interactive live editing of your Freestyle dev server
With Anthropic AI and Morph fast apply integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import freestyle
import os
import json
from datetime import datetime
import anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure CORS - for development allow all origins, for production specify React app origin
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"])

# Initialize API clients
anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

morph_client = OpenAI(
    api_key=os.getenv('MORPH_API_KEY'),
    base_url="https://api.morphllm.com/v1"
)

# Global variable to store the dev server connection
dev_server_wrapper = None

class DevServerWrapper:
    def __init__(self, dev_server):
        self.dev_server = dev_server
    
    def read_gamezone(self):
        return self.dev_server.fs.read_file("src/GameZone.js")
    
    def write_gamezone(self, content):
        self.dev_server.fs.write_file("src/GameZone.js", content)
        return True
    
    def update_gamezone_with_game(self, game_name):
        """Update GameZone.js with a new game name"""
        new_content = f'''import React from 'react';

const GameZone = ({{ currentGame }}) => {{
  return (
    <div className="game-zone">
      <div className="game-content">
        <h2>{game_name}</h2>
        <p>🎮 Welcome to {game_name}!</p>
        <div style={{{{
          background: 'linear-gradient(45deg, #ff6b6b, #4ecdc4)',
          padding: '15px',
          borderRadius: '8px',
          color: 'white',
          margin: '15px 0',
          textAlign: 'center',
          fontWeight: 'bold'
        }}}}>
          🎯 Current Game: {game_name}
          <br />
          Updated at: {datetime.now().strftime("%H:%M:%S")}
        </div>
        <p>🚀 Live updated via Flask API!</p>
      </div>
    </div>
  );
}};

export default GameZone;'''
        
        self.write_gamezone(new_content)
        return True

@app.route('/')
def home():
    """Home page with API documentation"""
    status = "Connected" if dev_server_wrapper else "Not Connected"
    
    docs = {
        "message": "Freestyle Live Edit Flask Server",
        "status": status,
        "endpoints": {
            "/": "This documentation",
            "/connect": "POST - Connect to GitHub repo and start dev server",
            "/status": "GET - Check connection status",
            "/gamezone/read": "GET - Read current GameZone.js content",
            "/gamezone/update": "POST - Update GameZone with new game name (JSON: {'game_name': 'YourGame'})",
            "/gamezone/write": "POST - Write custom content to GameZone.js (JSON: {'content': 'your_content'})",
            "/generate-game": "POST - Generate AI game from idea (JSON: {'game_idea': 'snake game'})"
        }
    }
    
    if dev_server_wrapper:
        docs["dev_server"] = {
            "app_url": dev_server_wrapper.dev_server.ephemeral_url,
            "vscode_url": dev_server_wrapper.dev_server.code_server_url
        }
    
    return jsonify(docs)

@app.route('/connect', methods=['POST'])
def connect_to_repo():
    """Connect to GitHub repo and create dev server"""
    global dev_server_wrapper
    
    try:
        client = freestyle.Freestyle(os.getenv('FREESTYLE_API_KEY'))
        
        print("🔗 Setting up dev server for yc-hack repo...")
        
        # Create/connect to the repo from GitHub
        repo = client.create_repository(
            name="yc-hack-live",
            public=True,
            source=freestyle.CreateRepoSource.from_dict({
                "type": "git", 
                "url": "https://github.com/shreybirmiwal/yc-hack"
            })
        )
        
        print(f"✅ Repository connected: {repo.repo_id}")
        
        # Request dev server for this repo
        dev_server = client.request_dev_server(repo_id=repo.repo_id)
        
        print(f"✅ Dev server ready!")
        
        # Create wrapper
        dev_server_wrapper = DevServerWrapper(dev_server)
        
        return jsonify({
            "success": True,
            "message": "Successfully connected to dev server",
            "repo_id": repo.repo_id,
            "app_url": dev_server.ephemeral_url,
            "vscode_url": dev_server.code_server_url
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/status')
def get_status():
    """Get current connection status"""
    if dev_server_wrapper:
        return jsonify({
            "connected": True,
            "app_url": dev_server_wrapper.dev_server.ephemeral_url,
            "vscode_url": dev_server_wrapper.dev_server.code_server_url
        })
    else:
        return jsonify({
            "connected": False,
            "message": "No dev server connected. Use POST /connect to connect."
        })

@app.route('/gamezone/read')
def read_gamezone():
    """Read current GameZone.js content"""
    if not dev_server_wrapper:
        return jsonify({"error": "Not connected to dev server"}), 400
    
    try:
        content = dev_server_wrapper.read_gamezone()
        return jsonify({
            "success": True,
            "content": content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gamezone/update', methods=['POST'])
def update_gamezone():
    """Update GameZone.js with new game name"""
    if not dev_server_wrapper:
        return jsonify({"error": "Not connected to dev server"}), 400
    
    data = request.get_json()
    if not data or 'game_name' not in data:
        return jsonify({"error": "Missing 'game_name' in request body"}), 400
    
    game_name = data['game_name']
    
    try:
        dev_server_wrapper.update_gamezone_with_game(game_name)
        return jsonify({
            "success": True,
            "message": f"GameZone updated with game: {game_name}",
            "app_url": dev_server_wrapper.dev_server.ephemeral_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gamezone/write', methods=['POST'])
def write_gamezone():
    """Write custom content to GameZone.js"""
    if not dev_server_wrapper:
        return jsonify({"error": "Not connected to dev server"}), 400
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Missing 'content' in request body"}), 400
    
    content = data['content']
    
    try:
        dev_server_wrapper.write_gamezone(content)
        return jsonify({
            "success": True,
            "message": "GameZone.js updated with custom content",
            "app_url": dev_server_wrapper.dev_server.ephemeral_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-game', methods=['POST'])
def generate_game():
    """Generate AI game using Anthropic and deploy via Morph + Freestyle"""
    if not dev_server_wrapper:
        return jsonify({"error": "Not connected to dev server. Use POST /connect first"}), 400
    
    data = request.get_json()
    if not data or 'game_idea' not in data:
        return jsonify({"error": "Missing 'game_idea' in request body"}), 400
    
    game_idea = data['game_idea']
    
    try:
        print(f"🎮 Generating game: {game_idea}")
        
        # Step 1: Generate game code with Anthropic
        game_code = generate_game_with_anthropic(game_idea)
        if not game_code:
            return jsonify({"error": "Failed to generate game code"}), 500
        
        # Step 2: Apply code with Morph
        applied_code = apply_code_with_morph(game_code, game_idea)
        if not applied_code:
            return jsonify({"error": "Failed to apply code changes"}), 500
        
        # Step 3: Deploy to Freestyle
        if deploy_to_freestyle(applied_code):
            return jsonify({
                "success": True,
                "message": f"Game '{game_idea}' generated and deployed successfully!",
                "game_idea": game_idea,
                "app_url": dev_server_wrapper.dev_server.ephemeral_url
            })
        else:
            return jsonify({"error": "Failed to deploy to Freestyle"}), 500
            
    except Exception as e:
        print(f"Error generating game: {e}")
        return jsonify({"error": str(e)}), 500

def generate_game_with_anthropic(game_idea):
    """Generate React game code using Anthropic API"""
    try:
        system_prompt = """You are a React game developer. Generate complete, working React component code for games. 
        The code should be a single React functional component that can replace the GameZone component.
        Include inline styles for a complete, playable game experience.
        Use only React hooks and standard JavaScript - no external game libraries.
        Make the game interactive and fun within a 400x300 pixel area."""
        
        user_prompt = f"""Create a {game_idea} game as a React component. 
        Requirements:
        - Named export as GameZone component
        - Accept currentGame prop (but can ignore it)
        - Fully playable game with controls
        - Use inline styles for all styling
        - Include game state, scoring, and basic game loop
        - Responsive to user input (keyboard/mouse)
        - Should be fun and engaging
        
        Return only the complete React component code, no explanations."""

        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )
        
        return message.content[0].text
        
    except Exception as e:
        print(f"Error generating game code: {e}")
        return None

def apply_code_with_morph(generated_code, instruction):
    """Apply code changes using Morph's fast apply"""
    try:
        # Read current GameZone.js from Freestyle dev server
        original_code = dev_server_wrapper.read_gamezone()
        
        instruction_text = f"I will replace the GameZone component with a new {instruction} game implementation"
        
        response = morph_client.chat.completions.create(
            model="morph-v3-large",
            messages=[{
                "role": "user", 
                "content": f"<instruction>{instruction_text}</instruction>\n<code>{original_code}</code>\n<update>{generated_code}</update>"
            }]
        )
        
        applied_code = response.choices[0].message.content
        return applied_code
        
    except Exception as e:
        print(f"Error applying code with Morph: {e}")
        return None

def deploy_to_freestyle(code):
    """Deploy code to Freestyle dev server"""
    try:
        dev_server_wrapper.write_gamezone(code)
        print("✅ Code deployed to Freestyle dev server")
        return True
        
    except Exception as e:
        print(f"Error deploying to Freestyle: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Freestyle Live Edit Flask Server with AI Game Generation...")
    print("📖 Visit http://localhost:8080 for API documentation")
    print("🔗 Use POST /connect to connect to your GitHub repo")
    print("🎮 Use POST /generate-game with {'game_idea': 'snake game'} to generate AI games")
    print("🔧 Use POST /gamezone/update with {'game_name': 'YourGame'} for simple updates")
    
    app.run(debug=True, host='0.0.0.0', port=8080)