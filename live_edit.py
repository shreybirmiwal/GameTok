#!/usr/bin/env python3
"""
Interactive live editing for your Freestyle dev server
"""

from freestyle_setup import SimpleFreestyle
import freestyle
import os

def get_existing_dev_server():
    """Connect to or create dev server for your yc-hack repo"""
    client = freestyle.Freestyle(os.getenv('FREESTYLE_API_KEY'))
    
    print("🔗 Setting up dev server for yc-hack repo...")
    
    try:
        # First, try to create/connect to the repo from your GitHub
        print("📋 Creating/connecting to yc-hack repository...")
        
        repo = client.create_repository(
            name="yc-hack-live",
            public=True,
            source=freestyle.CreateRepoSource.from_dict({
                "type": "git", 
                "url": "https://github.com/shreybirmiwal/yc-hack"
            })
        )
        
        print(f"✅ Repository connected: {repo.repo_id}")
        
        # Now request dev server for this repo
        print("🚀 Requesting dev server...")
        dev_server = client.request_dev_server(repo_id=repo.repo_id)
        
        print(f"✅ Dev server ready!")
        print(f"🌐 Your app: {dev_server.ephemeral_url}")
        print(f"💻 VSCode: {dev_server.code_server_url}")
        
        # Create a wrapper class to maintain compatibility
        class DevServerWrapper:
            def __init__(self, dev_server):
                self.dev_server = dev_server
            
            def read_gamezone(self):
                return self.dev_server.fs.read_file("src/GameZone.js")
            
            def write_gamezone(self, content):
                self.dev_server.fs.write_file("src/GameZone.js", content)
                print("✅ GameZone.js updated live!")
        
        return DevServerWrapper(dev_server)
        
    except Exception as e:
        print(f"❌ Could not setup dev server: {e}")
        return None

def demo_live_edit(fs):
    """Demo live editing GameZone.js"""
    if not fs:
        return
    
    print("\n📖 Current GameZone.js:")
    current_content = fs.read_gamezone()
    print(current_content[:200] + "..." if len(current_content) > 200 else current_content)
    
    print("\n✏️  Let's make a live edit!")
    
    # Create new content with live edit indicator
    new_content = '''import React from 'react';

const GameZone = ({ currentGame }) => {
  return (
    <div className="game-zone">
      <div className="game-content">
        <h2>{currentGame || "🚀 LIVE EDITED!"}</h2>
        <p>🎮 This was just edited LIVE!</p>
        <div style={{
          background: 'linear-gradient(45deg, #ff6b6b, #4ecdc4)',
          padding: '15px',
          borderRadius: '8px',
          color: 'white',
          margin: '15px 0',
          textAlign: 'center',
          fontWeight: 'bold'
        }}>
          ✨ LIVE EDIT DEMO ✨
          <br />
          Edited at: {new Date().toLocaleTimeString()}
        </div>
        <p>🔥 Refresh your browser to see this change!</p>
      </div>
    </div>
  );
};

export default GameZone;'''
    
    # Write the new content
    fs.write_gamezone(new_content)
    
    print(f"\n🎉 Live edit complete!")
    print(f"🌐 Check your app: {fs.dev_server.ephemeral_url}")
    print("🔄 The change should appear instantly (React hot reload)!")
    
    return fs

def interactive_edit(fs):
    """Interactive editing session"""
    if not fs:
        return
        
    print(f"\n🎮 Interactive Live Editing Session")
    print(f"🌐 Your app: {fs.dev_server.ephemeral_url}")
    print("💡 Try these commands:")
    print("- fs.read_gamezone() - Read current GameZone.js")
    print("- fs.write_gamezone(new_content) - Write new content")
    print("- fs.dev_server.fs.read_file('src/App.js') - Read any file")
    print("- fs.dev_server.fs.write_file('src/App.js', content) - Write any file")
    
    return fs

if __name__ == "__main__":
    # Connect to dev server
    fs = get_existing_dev_server()
    
    if fs:
        # Demo live edit
        fs = demo_live_edit(fs)
        
        # Start interactive session
        fs = interactive_edit(fs)
        
        print(f"\n✅ fs object is ready for live editing!")
        print("You can now call fs.read_gamezone() and fs.write_gamezone() directly")
        
        # Keep the object available
        globals()['fs'] = fs