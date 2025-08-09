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
        <p>Welcome to {game_name}!</p>
        <div style={{{{
          background: 'linear-gradient(45deg, #ff6b6b, #4ecdc4)',
          padding: '15px',
          borderRadius: '8px',
          color: 'white',
          margin: '15px 0',
          textAlign: 'center',
          fontWeight: 'bold'
        }}}}>
          Current Game: {game_name}
          <br />
          Updated at: {datetime.now().strftime("%H:%M:%S")}
        </div>
        <p>Live updated via Flask API!</p>
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
            "/generate-html-game": "POST - Generate HTML5 Canvas game (JSON: {'game_idea': 'snake'}) - perfect for Morph apply to GameZone!"
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
    """Generate AI HTML5 Canvas game using Anthropic and deploy via Morph + Freestyle"""
    if not dev_server_wrapper:
        return jsonify({"error": "Not connected to dev server. Use POST /connect first"}), 400
    
    data = request.get_json()
    if not data or 'game_idea' not in data:
        return jsonify({"error": "Missing 'game_idea' in request body"}), 400
    
    game_idea = data['game_idea']
    
    try:
        print(f"🎮 Generating game: {game_idea}")
        
        # Step 1: Generate HTML5 game with Anthropic
        game_html = generate_game_with_anthropic(game_idea)
        if not game_html:
            return jsonify({"error": "Failed to generate game HTML"}), 500
        
        # Step 2: Wrap HTML in React component
        applied_code = apply_code_with_morph(game_html, game_idea)
        if not applied_code:
            return jsonify({"error": "Failed to create React wrapper"}), 500
        
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

@app.route('/generate-html-game', methods=['POST'])
def generate_html_game():
    """Generate pure HTML5 Canvas game for direct injection - perfect for Morph apply!"""
    if not dev_server_wrapper:
        return jsonify({"error": "Not connected to dev server. Use POST /connect first"}), 400
    
    data = request.get_json()
    if not data or 'game_idea' not in data:
        return jsonify({"error": "Missing 'game_idea' in request body"}), 400
    
    game_idea = data['game_idea']
    
    try:
        print(f"🎮 Generating pure HTML game: {game_idea}")
        
        # Generate pure HTML5 game with Anthropic
        game_html = generate_game_with_anthropic(game_idea)
        if not game_html:
            return jsonify({"error": "Failed to generate game HTML"}), 500
        
        # Deploy HTML directly to Freestyle (no React wrapper needed)
        if deploy_html_to_freestyle(game_html, game_idea):
            return jsonify({
                "success": True,
                "message": f"Pure HTML game '{game_idea}' generated and deployed successfully!",
                "game_idea": game_idea,
                "app_url": dev_server_wrapper.dev_server.ephemeral_url,
                "html_content": game_html[:200] + "..." if len(game_html) > 200 else game_html
            })
        else:
            return jsonify({"error": "Failed to deploy HTML to Freestyle"}), 500
            
    except Exception as e:
        print(f"Error generating HTML game: {e}")
        return jsonify({"error": str(e)}), 500

def generate_game_with_anthropic(game_idea):
    """Generate completely self-contained HTML5 Canvas game using Anthropic API - zero dependencies"""
    try:
        system_prompt = """You are an HTML5 Canvas game developer. Generate complete, working HTML5 Canvas games. 
        CRITICAL: The game MUST work as a single standalone HTML snippet with ZERO external dependencies.
        Use ONLY HTML5 Canvas, vanilla JavaScript, and built-in browser APIs.
        NO external libraries, NO frameworks, NO dependencies whatsoever.
        The game will be directly injected into a React component's div as innerHTML."""
        
        user_prompt = f"""Create a {game_idea} game using HTML5 Canvas and vanilla JavaScript. 
        STRICT Requirements:
        - Complete HTML snippet with canvas, script, and inline styles
        - ZERO external dependencies - only vanilla JavaScript and Canvas API
        - Canvas size should be exactly 400x300 pixels
        - Include complete game state, scoring, game loop, and controls
        - Handle keyboard/mouse input appropriately
        - Use requestAnimationFrame for smooth animation
        - All styles must be inline CSS within <style> tags
        - Must be a complete, playable, engaging game
        - Include game over conditions and restart functionality
        
        Format: Return a complete HTML snippet like this:
        <div style="text-align: center;">
            <canvas id="gameCanvas" width="400" height="300" style="border: 2px solid #333;"></canvas>
            <div>Score: <span id="score">0</span></div>
            <div>Instructions: [game controls]</div>
        </div>
        <script>
        // Complete game logic here
        </script>
        
        IMPORTANT: This HTML will be injected directly into a React component - it must be 100% self-contained and work immediately.
        Return ONLY the complete HTML snippet, no explanations or markdown formatting.
        """

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

def apply_code_with_morph(generated_html, instruction):
    """Convert HTML5 game to React component using Morph's fast apply"""
    try:
        # Create a React component that renders the HTML game
        # Escape the HTML content properly
        escaped_html = generated_html.replace('`', '\\`').replace('${', '\\${')
        
        react_wrapper = f'''import React, {{ useEffect }} from 'react';

const GameZone = ({{ currentGame }}) => {{
  useEffect(() => {{
    // Re-initialize game when component mounts or updates
    const canvas = document.getElementById('gameCanvas');
    if (canvas) {{
      // Clear any existing game loops or event listeners
      // The game script will handle initialization
    }}
  }}, []);

  return (
    <div className="game-zone">
      <h2 style={{{{ textAlign: 'center', marginBottom: '15px' }}}}>
        {{currentGame || '{instruction}'}}
      </h2>
      <div 
        dangerouslySetInnerHTML={{{{ __html: `{escaped_html}` }}}}
      />
    </div>
  );
}};

export default GameZone;'''
        
        return react_wrapper
        
    except Exception as e:
        print(f"Error creating React wrapper: {e}")
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

def deploy_html_to_freestyle(html_content, game_name):
    """Deploy pure HTML content to Freestyle dev server by updating GameZone"""
    try:
        # Escape HTML content for embedding in React
        escaped_html = html_content.replace('`', '\\`').replace('${', '\\${')
        
        # Create a simple React component that renders the HTML
        react_component = f'''import React from 'react';

const GameZone = ({{ currentGame }}) => {{
  return (
    <div className="game-zone">
      <div className="game-content">
        <h2 style={{{{ textAlign: 'center', marginBottom: '15px' }}}}>
          {game_name}
        </h2>
        <div dangerouslySetInnerHTML={{{{ __html: `{escaped_html}` }}}} />
        <div style={{{{ textAlign: 'center', marginTop: '10px', fontSize: '12px', color: '#666' }}}}>
          🎮 Generated with HTML5 Canvas | Perfect for Morph apply!
        </div>
      </div>
    </div>
  );
}};

export default GameZone;'''
        
        dev_server_wrapper.write_gamezone(react_component)
        print("✅ HTML game deployed to Freestyle dev server")
        return True
        
    except Exception as e:
        print(f"Error deploying HTML to Freestyle: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Freestyle Live Edit Flask Server with HTML5 Game Generation...")
    print("📖 Visit http://localhost:8080 for API documentation")
    print("🔗 Use POST /connect to connect to your GitHub repo")
    print("🎮 Use POST /generate-html-game with {'game_idea': 'snake'} to generate games for Morph apply")
    print("🔧 GameZone.js is now a simple HTML renderer - perfect for Morph apply!")
    
    app.run(debug=True, host='0.0.0.0', port=8080)