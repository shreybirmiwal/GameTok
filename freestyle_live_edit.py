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
import re
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

# In-memory debug snapshot of the last generation and apply
last_generation_debug = {
    "idea": None,
    "timestamp": None,
    # Claude outputs
    "claude_code_raw": None,
    "claude_code": None,  # sanitized
    # Before/after
    "before_code": None,
    "morph_code_raw": None,
    "morph_code": None,   # sanitized
    "written_code": None
}

# --------------------
# Sanitization helpers
# --------------------

def strip_markdown_fences(text: str) -> (str, bool):
    """Remove markdown code fences like ```js ... ``` and return (stripped, was_stripped)."""
    if text is None:
        return text, False
    if "```" not in text:
        return text, False
    # Capture the largest fenced block if multiple
    matches = list(re.finditer(r"```[a-zA-Z0-9_\-]*\n", text))
    if not matches:
        # Fallback: remove any bare fences
        return text.replace("```", ""), True
    start = matches[0].end()
    end_idx = text.rfind("```")
    if end_idx > start:
        inner = text[start:end_idx]
        return inner.strip(), True
    return text.replace("```", ""), True


def ensure_react_file_contract(code: str) -> (str, list):
    """Ensure the file starts with a React import and ends with export default GameZone.
    Returns (possibly fixed code, list_of_fixes)."""
    fixes = []
    if code is None:
        return code, fixes
    normalized = code.lstrip("\ufeff")  # strip BOM if present
    # Ensure import
    first_300 = normalized[:300]
    if "import React" not in first_300:
        normalized = (
            "import React, { useEffect, useRef, useState } from 'react';\n" + normalized
        )
        fixes.append("added_import")
    # Ensure export default
    if "export default GameZone" not in normalized:
        normalized = normalized.rstrip() + "\n\nexport default GameZone;\n"
        fixes.append("added_export")
    return normalized, fixes


def sanitize_react_code(raw: str, source_label: str) -> (str, dict):
    """Strip fences and enforce React file contract. Returns (sanitized, meta)."""
    meta = {"source": source_label, "stripped_fences": False, "fixes": []}
    code = raw or ""
    code, stripped = strip_markdown_fences(code)
    meta["stripped_fences"] = stripped
    code, fixes = ensure_react_file_contract(code)
    meta["fixes"] = fixes
    if stripped or fixes:
        logger.warning(f"Sanitized {source_label}: stripped_fences={stripped}, fixes={fixes}")
    return code, meta

# --------------------
# Dev server wrapper
# --------------------

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
            "/game-log": "GET - View recent game generation logs",
            "/detailed-log": "GET - View detailed game code and before/after comparisons",
            "/last-debug": "GET - View last Claude output, Morph result, and written code"
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
        # snapshot Claude output
        last_generation_debug["idea"] = game_idea
        last_generation_debug["timestamp"] = datetime.now().isoformat()
        last_generation_debug["claude_code_raw"] = game_html # Store raw
        last_generation_debug["claude_code"], _ = sanitize_react_code(game_html, "Claude") # Store sanitized
        if not last_generation_debug["claude_code"]:
            logger.error(f"❌ Claude generation FAILED for: '{game_idea}'")
            return jsonify({"error": "Failed to generate game HTML"}), 500
        
        # Log game details and actual generated code
        game_length = len(game_html)
        has_canvas = "<canvas" in game_html.lower()
        has_script = "<script" in game_html.lower()
        logger.info(f"✅ Claude generated game - Length: {game_length} chars, Has Canvas: {has_canvas}, Has Script: {has_script}")
        
        # Log the actual generated game code (truncated for readability)
        game_preview = game_html[:500] + "..." if len(game_html) > 500 else game_html
        logger.info(f"🎮 GENERATED GAME CODE for '{game_idea}':\n{'-'*50}\n{game_preview}\n{'-'*50}")
        
        # Save full game code to detailed log file
        try:
            with open('detailed_game_logs.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"GAME GENERATION: {game_idea} - {datetime.now()}\n")
                f.write(f"{'='*80}\n")
                f.write(f"FULL CLAUDE GENERATED CODE:\n{'-'*40}\n")
                f.write(game_html)
                f.write(f"\n{'-'*40}\n\n")
        except Exception as e:
            logger.error(f"❌ Failed to write detailed log: {e}")
        
        # Step 2: Use Morph to replace GameZone.js with React component
        logger.info(f"⚡ Applying React component to GameZone.js using Morph for: '{game_idea}'")
        if apply_react_with_morph_to_gamezone(last_generation_debug["claude_code"], game_idea):
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

@app.route('/generate-idea', methods=['POST'])
def generate_idea():
    """Generate a short, simple, descriptive arcade-style game idea using Anthropic.
    Returns JSON: {"idea": "..."}
    """
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt') or (
            "Generate an implementation-ready, tiny HTML5 canvas game idea that an LLM can build in one pass with 100% accuracy. "
            "Return a single line formatted as: \"<Title>: <explicit mechanic spec>\". "
            "Keep the title short, but make the mechanic spec explicit (1–2 sentences max) with concrete controls and numbers."
        )
        recent_ideas = data.get('recentIdeas') or []

        system_prompt = (
            "You are a creative assistant producing implementation-ready specs for tiny HTML5 canvas games. "
            "Output must be ONE line idea suitable for a quick canvas prototype. The mechanic spec MUST include: "
            "- exact control scheme (e.g., Arrow keys to move, Space to jump) "
            "- clear win/lose or score condition "
            "- concrete parameters (e.g., speeds, spawn rates, sizes) where relevant "
            "Avoid vague pitches (e.g., 'neon dodge')."
        )

        # Compose user prompt with recent ideas to avoid duplicates
        avoid = ("\nRecent ideas (avoid repeating):\n- " + "\n- ".join(recent_ideas)) if recent_ideas else ""
        user_prompt = f"{prompt}{avoid}\nReturn only one line with the exact format '<Title>: <explicit mechanic spec>'. No extra text."

        idea_text = None
        try:
            message = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=128,
                temperature=0.8,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            idea_text = (message.content[0].text or '').strip()
        except Exception as e:
            logger.warning(f"Anthropic idea generation failed: {e}")
            idea_text = None

        if not idea_text:
            # Local fallback
            adjectives = ['Tiny', 'Cosmic', 'Retro', 'Neon', 'Shadow', 'Pixel', 'Turbo', 'Mystic', 'Swift', 'Lucky']
            nouns = ['Runner', 'Climber', 'Racer', 'Dodger', 'Miner', 'Glider', 'Jumper', 'Fisher', 'Courier', 'Knight']
            mechanics = [
                'tap to jump over obstacles and collect coins',
                'hold to charge a jump and time landings on moving platforms',
                'swipe to change lanes and avoid traffic',
                'drag to slingshot between anchors while avoiding spikes',
                'tap to hook and swing past gaps',
                'tap to dive and resurface to collect treasures',
                'hold-and-release to dash through breakable walls',
                'tap to flip gravity and stay on the track',
                'tap to fish and upgrade your rod between runs',
                'tap to deliver packages while dodging drones',
            ]
            worlds = ['in a neon city', 'in a haunted forest', 'on floating islands', 'in retro space', 'inside a cave', 'on rooftops']
            import random
            for _ in range(5):
                idea_text = f"{random.choice(adjectives)} {random.choice(nouns)}: {random.choice(mechanics)} {random.choice(worlds)}."
                if idea_text not in recent_ideas:
                    break

        return jsonify({"idea": idea_text})
    except Exception as e:
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

@app.route('/detailed-log')
def get_detailed_log():
    """Get detailed game code and before/after comparisons"""
    try:
        if os.path.exists('detailed_game_logs.txt'):
            with open('detailed_game_logs.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                # Split into individual game generations
                games = content.split('=' * 80)
                # Get last 3 game generations to avoid overwhelming response
                recent_games = games[-3:] if len(games) > 3 else games
                return jsonify({
                    "success": True,
                    "total_games": len(games) - 1,  # Subtract 1 for empty first split
                    "recent_detailed_logs": recent_games
                })
        else:
            return jsonify({
                "success": True,
                "message": "No detailed game log file found yet",
                "recent_detailed_logs": []
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Removed duplicate /generate-html-game endpoint - using /generate-game instead

@app.route('/last-debug')
def get_last_debug():
    """Return the last generation/apply snapshot including full code blocks"""
    try:
        return jsonify({
            "success": True,
            "debug": last_generation_debug
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_game_with_anthropic(game_idea):
    """Generate a complete, self-contained React GameZone component using Anthropic API - zero dependencies beyond React"""
    try:
        logger.info(f"🤖 Claude generation starting for: '{game_idea}'")
        
        system_prompt = """You are a React game developer. Generate a complete, self-contained React functional component called GameZone that can be saved directly as src/GameZone.js.
        HARD REQUIREMENTS (do not violate):
        - Output MUST be valid JavaScript/JSX only.
        - DO NOT include markdown fences (no ```js, no ```json, no ```).
        - DO NOT include explanations or comments outside the code.
        - Only import React hooks; no external packages.
        - Inline styles only; no CSS files.
        - Export default the component.
        - Keep the play area near 400x300 and keep mechanics simple.
        """
        
        user_prompt = f"""Create a SIMPLE {game_idea} game as a React functional component that REPLACES the entire contents of src/GameZone.js.
        Requirements (must follow exactly):
        - Component name: GameZone; prop: currentGame (may be unused)
        - No document.getElementById; if using canvas, useRef + useEffect
        - No external libs; only React
        - Inline styles; no classes
        - Provide restart/reset in the component
        - Return ONLY the full file contents of GameZone.js (imports + component + export default).
        - DO NOT wrap the code in markdown fences or any prose.
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

def apply_react_with_morph_to_gamezone(react_code, game_name):
    """Use Morph to replace entire GameZone.js with a React component"""
    try:
        # Read current GameZone.js
        current_gamezone = dev_server_wrapper.read_gamezone()
        logger.info(f"📖 Read current GameZone.js - Size: {len(current_gamezone)} chars")
        last_generation_debug["before_code"] = current_gamezone
        
        instruction = f"""I am replacing the entire contents of src/GameZone.js with a new React component implementing '{game_name}'.
        This is a single edit to one file. Return ONLY the final code for src/GameZone.js.
        CRITICAL:
        - Keep file path the same (src/GameZone.js)
        - Ensure the file starts with the correct React import and ends with `export default GameZone;`
        - Do NOT include any markdown fences, explanations, or extra text
        """
        
        logger.info(f"⚡ Sending React component to Morph fast apply - Game: '{game_name}', size: {len(react_code)} chars")
        response = morph_client.chat.completions.create(
            model="morph-v3-large",
            messages=[{
                "role": "user",
                "content": f"<instruction>{instruction}</instruction>\n<code>{current_gamezone}</code>\n<update>{react_code}</update>"
            }]
        )
        
        updated_gamezone_raw = response.choices[0].message.content
        updated_gamezone, _meta = sanitize_react_code(updated_gamezone_raw, "Morph")
        logger.info(f"✅ Morph returned updated React component - New size: {len(updated_gamezone)} chars")
        last_generation_debug["morph_code_raw"] = updated_gamezone_raw
        last_generation_debug["morph_code"] = updated_gamezone
        
        dev_server_wrapper.write_gamezone(updated_gamezone)
        last_generation_debug["written_code"] = updated_gamezone
        logger.info(f"📝 Written new React GameZone to Freestyle - Game: '{game_name}'")
        return True
    
    except Exception as e:
        logger.error(f"❌ Morph React apply error for '{game_name}': {str(e)}")
        return False
        
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
    print("🔍 Detailed code logging enabled - View at GET /detailed-log")
    
    app.run(debug=True, host='0.0.0.0', port=8080)