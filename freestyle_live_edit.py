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
import logging
from datetime import datetime
import anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup logging for game generation tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
            "/generate-game": "POST - Generate HTML5 Canvas game (JSON: {'game_idea': 'snake'}) - Claude generates, Morph applies!",
            "/game-log": "GET - View recent game generation logs"
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
        start_time = datetime.now()
        print(f"🎮 Generating game: {game_idea}")
        logger.info(f"🎮 GAME GENERATION STARTED - Idea: '{game_idea}' - Timestamp: {start_time}")
        
        # Step 1: Generate HTML5 game with Anthropic
        logger.info(f"📝 Calling Claude to generate HTML5 Canvas game for: '{game_idea}'")
        game_html = generate_game_with_anthropic(game_idea)
        if not game_html:
            logger.error(f"❌ Claude generation FAILED for: '{game_idea}'")
            return jsonify({"error": "Failed to generate game HTML"}), 500
        
        # Log game details
        game_length = len(game_html)
        has_canvas = "<canvas" in game_html.lower()
        has_script = "<script" in game_html.lower()
        logger.info(f"✅ Claude generated game - Length: {game_length} chars, Has Canvas: {has_canvas}, Has Script: {has_script}")
        
        # Step 2: Use Morph to apply HTML to GameZone  
        logger.info(f"⚡ Applying game to GameZone.js using Morph for: '{game_idea}'")
        if apply_html_with_morph_to_gamezone(game_html, game_idea):
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"🎉 GAME GENERATION SUCCESS - '{game_idea}' - Duration: {duration:.2f}s - Size: {game_length} chars")
            
            return jsonify({
                "success": True,
                "message": f"Game '{game_idea}' generated and deployed successfully!",
                "game_idea": game_idea,
                "app_url": dev_server_wrapper.dev_server.ephemeral_url,
                "generation_time": f"{duration:.2f}s",
                "game_size": game_length
            })
        else:
            logger.error(f"❌ Morph apply FAILED for: '{game_idea}'")
            return jsonify({"error": "Failed to deploy to Freestyle"}), 500
            
    except Exception as e:
        logger.error(f"💥 GAME GENERATION ERROR for '{game_idea}': {str(e)}")
        print(f"Error generating game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/game-log')
def get_game_log():
    """Get recent game generation logs"""
    try:
        if os.path.exists('game_generation.log'):
            with open('game_generation.log', 'r') as f:
                lines = f.readlines()
                # Get last 50 lines for recent activity
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                return jsonify({
                    "success": True,
                    "log_lines": len(lines),
                    "recent_logs": [line.strip() for line in recent_lines]
                })
        else:
            return jsonify({
                "success": True,
                "message": "No game generation log file found yet",
                "recent_logs": []
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Removed duplicate /generate-html-game endpoint - using /generate-game instead

def generate_game_with_anthropic(game_idea):
    """Generate completely self-contained HTML5 Canvas game using Anthropic API - zero dependencies"""
    try:
        logger.info(f"🤖 Claude generation starting for: '{game_idea}'")
        
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

        logger.info(f"📡 Sending request to Claude for '{game_idea}' - Model: claude-sonnet-4-20250514")
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
        
        generated_content = message.content[0].text
        logger.info(f"✅ Claude generated content for '{game_idea}' - Length: {len(generated_content)} chars")
        
        # Log some details about what was generated
        content_lower = generated_content.lower()
        has_canvas = "<canvas" in content_lower
        has_script = "<script" in content_lower
        has_style = "<style" in content_lower or "style=" in content_lower
        logger.info(f"📊 Generated game analysis - Canvas: {has_canvas}, Script: {has_script}, Styles: {has_style}")
        
        return generated_content
        
    except Exception as e:
        logger.error(f"❌ Claude generation error for '{game_idea}': {str(e)}")
        print(f"Error generating game code: {e}")
        return None

# Removed unused functions: apply_code_with_morph() and deploy_to_freestyle()
# These were from the old approach before proper Morph integration

def apply_html_with_morph_to_gamezone(html_content, game_name):
    """Use Morph's fast apply to update GameZone.js with HTML game content"""
    try:
        # Read current GameZone.js
        current_gamezone = dev_server_wrapper.read_gamezone()
        logger.info(f"📖 Read current GameZone.js - Size: {len(current_gamezone)} chars")
        
        # Create instruction for Morph
        instruction = f"Replace the htmlContent variable in GameZone.js with the HTML5 Canvas game for '{game_name}'. Keep the same structure but update only the content inside the backticks."
        
        # Use Morph's fast apply
        logger.info(f"⚡ Sending to Morph fast apply - Game: '{game_name}', HTML size: {len(html_content)} chars")
        response = morph_client.chat.completions.create(
            model="morph-v3-large",  # Using Morph's fast apply model
            messages=[{
                "role": "user", 
                "content": f"<instruction>{instruction}</instruction>\n<code>{current_gamezone}</code>\n<update>The new htmlContent should be: `{html_content}`</update>"
            }]
        )
        
        # Get the updated code from Morph
        updated_gamezone = response.choices[0].message.content
        logger.info(f"✅ Morph returned updated code - New size: {len(updated_gamezone)} chars")
        
        # Apply the changes to Freestyle
        dev_server_wrapper.write_gamezone(updated_gamezone)
        logger.info(f"📝 Written to Freestyle dev server - Game: '{game_name}' successfully deployed")
        print(f"✅ Used Morph to apply HTML game '{game_name}' to GameZone.js")
        return True
        
    except Exception as e:
        logger.error(f"❌ Morph apply error for '{game_name}': {str(e)}")
        print(f"Error using Morph to apply HTML: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Freestyle Live Edit Flask Server with Claude + Morph Integration...")
    print("📖 Visit http://localhost:8080 for API documentation")
    print("🔗 Use POST /connect to connect to your GitHub repo")
    print("🎮 Use POST /generate-game with {'game_idea': 'snake'} - Claude generates, Morph applies!")
    print("⚡ Now using Morph's fast apply to update GameZone.js automatically!")
    print("📊 Game generation logging enabled - View logs at GET /game-log")
    
    app.run(debug=True, host='0.0.0.0', port=8080)