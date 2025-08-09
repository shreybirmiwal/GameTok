#!/usr/bin/env python3
"""
Simple Freestyle setup for yc-hack project
Does exactly what you need: connects, launches dev server, injects .env, gives you edit functions
"""

import os
import freestyle
from dotenv import load_dotenv

load_dotenv()

class SimpleFreestyle:
    def __init__(self):
        self.client = freestyle.Freestyle(os.getenv('FREESTYLE_API_KEY'))
        self.dev_server = None
        self.repo_id = None
    
    def setup(self):
        """1. Connect freestyle to this project and 2. Launch dev server"""
        print("🚀 Setting up Freestyle for yc-hack...")
        
        # Create repo from your GitHub
        repo = self.client.create_repository(
            name="yc-hack-live",
            public=True,
            source=freestyle.CreateRepoSource.from_dict({
                "type": "git", 
                "url": "https://github.com/shreybirmiwal/yc-hack"
            })
        )
        self.repo_id = repo.repo_id
        print(f"✅ Connected to your GitHub repo")
        
        # Launch dev server
        self.dev_server = self.client.request_dev_server(repo_id=self.repo_id)
        print(f"✅ Dev server launched: {self.dev_server.ephemeral_url}")
        
        return self.dev_server.ephemeral_url
    
    def inject_env(self):
        """3. Inject your .env from here to there"""
        with open('.env', 'r') as f:
            env_content = f.read()
        
        self.dev_server.fs.write_file(".env", env_content)
        print("✅ .env injected to dev server")
    
    def start_app(self):
        """Install and start the React app"""
        print("📦 Installing dependencies...")
        self.dev_server.process.exec("npm install")
        
        print("🚀 Starting React app...")
        self.dev_server.process.exec("npm run dev", background=True)
        print(f"✅ Your app is live: {self.dev_server.ephemeral_url}")
    
    def read_gamezone(self):
        """5. Read GameZone.js"""
        return self.dev_server.fs.read_file("src/GameZone.js")
    
    def write_gamezone(self, content):
        """5. Write to GameZone.js"""
        self.dev_server.fs.write_file("src/GameZone.js", content)
        print("✅ GameZone.js updated live!")

# Usage:
def main():
    fs = SimpleFreestyle()
    
    # Steps 1 & 2: Connect and launch
    url = fs.setup()
    
    # Step 3: Inject .env
    fs.inject_env()
    
    # Start the app
    fs.start_app()
    
    print(f"\n🎉 Done! Your app: {url}")
    print(f"💻 VSCode: {fs.dev_server.code_server_url}")
    
    # Step 5: Demo edit function
    print("\n📝 Demo: Reading GameZone.js...")
    current = fs.read_gamezone()
    print(f"Current GameZone has {len(current)} characters")
    
    return fs

if __name__ == "__main__":
    freestyle = main()
    print("\n✅ Ready! Use:")
    print("- freestyle.read_gamezone()")  
    print("- freestyle.write_gamezone(new_content)")