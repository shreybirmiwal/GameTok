#!/usr/bin/env python3
"""
Quick example of how to edit GameZone.js live on Freestyle dev server
"""

from freestyle_dev import FreestyleDevController

# Example: Quick edit function
def quick_edit_gamezone(repo_id, new_game_text="🎮 LIVE EDIT TEST! 🎮"):
    """Quickly edit GameZone with new content"""
    controller = FreestyleDevController()
    
    # Connect to existing dev server
    dev_server = controller.request_dev_server(repo_id)
    
    if not dev_server:
        print("❌ Could not connect to dev server")
        return
    
    # Create new GameZone content with the new text
    new_content = f'''import React from 'react';

const GameZone = ({{ currentGame }}) => {{
  return (
    <div className="game-zone">
      <div className="game-content">
        <h2>{{currentGame || "{new_game_text}"}}</h2>
        <p>🎮 Game will load here</p>
        <div style={{{{ 
          padding: '20px', 
          background: '#f0f0f0', 
          borderRadius: '8px', 
          margin: '10px 0' 
        }}}}>
          <p>✨ This was edited live via Freestyle! ✨</p>
          <p>Timestamp: {{new Date().toLocaleTimeString()}}</p>
        </div>
      </div>
    </div>
  );
}};

export default GameZone;'''
    
    # Apply the edit
    if controller.edit_game_zone(new_content):
        print(f"✅ GameZone.js updated with: {new_game_text}")
        print(f"🌐 Check your changes at: {dev_server.ephemeral_url}")
        return True
    else:
        print("❌ Failed to update GameZone.js")
        return False

# Example usage functions
def upload_env_to_server(repo_id):
    """Upload .env file to running dev server"""
    controller = FreestyleDevController()
    dev_server = controller.request_dev_server(repo_id)
    
    if dev_server and controller.upload_env_file():
        print("✅ .env file uploaded successfully")
        return True
    return False

def add_new_game_to_list(repo_id, game_name):
    """Add a new game to the games array in App.js"""
    controller = FreestyleDevController()
    dev_server = controller.request_dev_server(repo_id)
    
    if not dev_server:
        return False
    
    # Read current App.js
    current_app = controller.read_file("src/App.js")
    if not current_app:
        return False
    
    # Add new game to the games array (simple string replacement)
    games_section = '''const games = [
    "Snake Game - Eat the apples!",
    "Pong - Classic paddle game",
    "Tetris - Stack the blocks",
    "Space Invaders - Defend Earth!",
    "Pac-Man - Eat all the dots",
    "Breakout - Break all the bricks",
    "Frogger - Cross the road safely"
  ];'''
    
    new_games_section = f'''const games = [
    "Snake Game - Eat the apples!",
    "Pong - Classic paddle game", 
    "Tetris - Stack the blocks",
    "Space Invaders - Defend Earth!",
    "Pac-Man - Eat all the dots",
    "Breakout - Break all the bricks",
    "Frogger - Cross the road safely",
    "{game_name}"
  ];'''
    
    updated_app = current_app.replace(games_section, new_games_section)
    
    # Write back to dev server
    try:
        dev_server.fs.write_file("src/App.js", updated_app)
        print(f"✅ Added new game: {game_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to add game: {e}")
        return False

if __name__ == "__main__":
    print("🎮 Freestyle Live Edit Examples")
    print("This script provides examples of live editing your React app")
    print("Run test_freestyle.py first to set up your dev server!")
    
    # Example calls (uncomment and provide repo_id to use):
    # quick_edit_gamezone("your-repo-id-here", "🚀 LIVE CODING IS AWESOME!")
    # upload_env_to_server("your-repo-id-here") 
    # add_new_game_to_list("your-repo-id-here", "Flappy Bird - Don't crash!")