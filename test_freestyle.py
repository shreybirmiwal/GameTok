#!/usr/bin/env python3
"""
Simple test script to demonstrate Freestyle dev server functionality
"""

from freestyle_dev import FreestyleDevController

def test_freestyle_connection():
    """Test the Freestyle connection and basic operations"""
    print("🚀 Starting Freestyle Dev Server Test...")
    
    # Initialize controller
    controller = FreestyleDevController()
    
    try:
        # Create repository (or use existing one)
        print("\n📁 Creating repository...")
        repo_id = controller.create_repository("YC-Hack-TikTok-Games")
        
        if repo_id:
            print(f"✅ Repository created: {repo_id}")
        else:
            print("❌ Failed to create repository")
            return
        
        # Request dev server
        print("\n🖥️  Requesting dev server...")
        dev_server = controller.request_dev_server()
        
        if dev_server:
            print("✅ Dev server is ready!")
            print(f"🌐 Live URL: {dev_server.ephemeral_url}")
            print(f"💻 VSCode Web: {dev_server.code_server_url}")
        else:
            print("❌ Failed to create dev server")
            return
        
        # Upload .env file
        print("\n📤 Uploading .env file...")
        if controller.upload_env_file():
            print("✅ .env file uploaded successfully")
        else:
            print("❌ Failed to upload .env file")
        
        # Edit GameZone.js with your current content
        print("\n✏️  Updating GameZone.js...")
        with open('src/GameZone.js', 'r') as f:
            current_gamezone = f.read()
        
        if controller.edit_game_zone(current_gamezone):
            print("✅ GameZone.js updated successfully")
        else:
            print("❌ Failed to update GameZone.js")
        
        # Upload your current App.js and App.css too
        print("\n📤 Uploading current React app files...")
        
        # Upload App.js
        with open('src/App.js', 'r') as f:
            app_js_content = f.read()
        controller.dev_server.fs.write_file("src/App.js", app_js_content)
        print("✅ App.js uploaded")
        
        # Upload App.css
        with open('src/App.css', 'r') as f:
            app_css_content = f.read()
        controller.dev_server.fs.write_file("src/App.css", app_css_content)
        print("✅ App.css uploaded")
        
        # Upload package.json
        with open('package.json', 'r') as f:
            package_json_content = f.read()
        controller.dev_server.fs.write_file("package.json", package_json_content)
        print("✅ package.json uploaded")
        
        # Install dependencies and start dev server
        print("\n📦 Installing dependencies...")
        controller.run_command("npm install")
        
        print("\n🚀 Starting dev server...")
        controller.run_command("npm run dev", background=True)
        
        print("\n🎉 SUCCESS! Your TikTok Games app is now running on Freestyle!")
        print(f"🌐 Visit: {dev_server.ephemereal_url}")
        print(f"💻 Edit in browser: {dev_server.code_server_url}")
        
        print("\n📝 You can now:")
        print("- Edit files using controller.edit_game_zone() or controller.dev_server.fs.write_file()")
        print("- Upload new files using controller.upload_env_file() or similar methods")
        print("- Run commands using controller.run_command()")
        print("- Commit changes using controller.commit_and_push()")
        
        return controller
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return None

if __name__ == "__main__":
    controller = test_freestyle_connection()
    
    if controller:
        print("\n🎮 Ready to edit your TikTok Games app live!")
        print("The controller object is available for further operations.")