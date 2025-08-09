#!/usr/bin/env python3
"""
Freestyle Dev Server Controller
Connects to Freestyle, creates a dev server, and provides functions to upload/edit files.
"""

import os
import freestyle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FreestyleDevController:
    def __init__(self):
        self.api_key = os.getenv('FREESTYLE_API_KEY')
        if not self.api_key:
            raise ValueError("FREESTYLE_API_KEY not found in environment")
        
        self.client = freestyle.Freestyle(self.api_key)
        self.repo_id = None
        self.dev_server = None
        
    def create_repository(self, name="YC-Hack-TikTok-Games"):
        """Create a new Git repository on Freestyle using your existing GitHub repo"""
        try:
            repo = self.client.create_repository(
                name=name,
                public=True,  # For testing - disable in production
                source=freestyle.CreateRepoSource.from_dict({
                    "type": "git",
                    "url": "https://github.com/shreybirmiwal/yc-hack"  # Your actual repo
                })
            )
            self.repo_id = repo.repo_id
            print(f"Created repo with ID: {self.repo_id}")
            print(f"Cloned from: https://github.com/shreybirmiwal/yc-hack")
            return self.repo_id
        except Exception as e:
            print(f"Error creating repository: {e}")
            return None
    
    def request_dev_server(self, repo_id=None):
        """Request a dev server for the repository"""
        if repo_id:
            self.repo_id = repo_id
        elif not self.repo_id:
            raise ValueError("No repository ID available. Create a repo first.")
            
        try:
            self.dev_server = self.client.request_dev_server(repo_id=self.repo_id)
            print(f"Dev Server URL: {self.dev_server.ephemeral_url}")
            print(f"MCP Server URL: {self.dev_server.mcp_ephemeral_url}")
            print(f"VSCode URL: {self.dev_server.code_server_url}")
            return self.dev_server
        except Exception as e:
            print(f"Error requesting dev server: {e}")
            return None
    
    def upload_env_file(self, env_content=None):
        """Upload .env file to the dev server"""
        if not self.dev_server:
            raise ValueError("No dev server available. Request one first.")
            
        if env_content is None:
            # Read from local .env file
            try:
                with open('.env', 'r') as f:
                    env_content = f.read()
            except FileNotFoundError:
                print("No .env file found locally")
                return False
        
        try:
            self.dev_server.fs.write_file(".env", env_content)
            print("Successfully uploaded .env file to dev server")
            return True
        except Exception as e:
            print(f"Error uploading .env file: {e}")
            return False
    
    def edit_game_zone(self, new_content):
        """Edit the GameZone.js file with new content"""
        if not self.dev_server:
            raise ValueError("No dev server available. Request one first.")
            
        try:
            # Write the new GameZone.js content
            self.dev_server.fs.write_file("src/GameZone.js", new_content)
            print("Successfully updated GameZone.js")
            return True
        except Exception as e:
            print(f"Error editing GameZone.js: {e}")
            return False
    
    def read_file(self, file_path):
        """Read a file from the dev server"""
        if not self.dev_server:
            raise ValueError("No dev server available. Request one first.")
            
        try:
            content = self.dev_server.fs.read_file(file_path)
            return content
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def list_files(self, directory="src"):
        """List files in a directory on the dev server"""
        if not self.dev_server:
            raise ValueError("No dev server available. Request one first.")
            
        try:
            files = self.dev_server.fs.ls(directory)
            return files
        except Exception as e:
            print(f"Error listing files in {directory}: {e}")
            return None
    
    def run_command(self, command, background=False):
        """Execute a command on the dev server"""
        if not self.dev_server:
            raise ValueError("No dev server available. Request one first.")
            
        try:
            result = self.dev_server.process.exec(command, background=background)
            if not background:
                print(f"Command output:\n{result.stdout}")
                if result.stderr:
                    print(f"Command errors:\n{result.stderr}")
            return result
        except Exception as e:
            print(f"Error running command '{command}': {e}")
            return None
    
    def commit_and_push(self, message):
        """Commit and push changes to the repository"""
        if not self.dev_server:
            raise ValueError("No dev server available. Request one first.")
            
        try:
            self.dev_server.commit_and_push(message)
            print(f"Successfully committed and pushed: {message}")
            return True
        except Exception as e:
            print(f"Error committing and pushing: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the dev server"""
        if self.dev_server:
            try:
                self.dev_server.shutdown()
                print("Dev server shut down successfully")
                return True
            except Exception as e:
                print(f"Error shutting down dev server: {e}")
                return False
        return True

def main():
    """Main function to demonstrate usage"""
    controller = FreestyleDevController()
    
    # Create repository
    repo_id = controller.create_repository("TikTok-Games-Demo")
    if not repo_id:
        return
    
    # Request dev server
    dev_server = controller.request_dev_server()
    if not dev_server:
        return
    
    # Upload .env file
    controller.upload_env_file()
    
    # Example: Edit GameZone.js with new content
    new_game_zone = '''import React from 'react';

const GameZone = ({ currentGame }) => {
  return (
    <div className="game-zone">
      <div className="game-content">
        <h2>{currentGame || "Welcome to Game Zone!"}</h2>
        <p>🎮 Live editing from Freestyle!</p>
        <div className="game-preview">
          <p>Game will load here via AI...</p>
        </div>
      </div>
    </div>
  );
};

export default GameZone;'''
    
    controller.edit_game_zone(new_game_zone)
    
    # List files to verify
    files = controller.list_files("src")
    print(f"Files in src/: {files}")
    
    print(f"\\n🚀 Dev server is running at: {dev_server.ephemeral_url}")
    print(f"📝 VSCode Web UI: {dev_server.code_server_url}")
    
    return controller

if __name__ == "__main__":
    controller = main()