"""
launch.py — Starts the Flask app and creates a live public URL via ngrok tunnel.
Run this script instead of `app.py` to get a shareable live link.

Usage:
    .venv\Scripts\python.exe launch.py
"""

import threading
import time
import sys
import os

def start_flask():
    """Run the Flask app in a thread."""
    # Import and run the Flask app
    os.environ["FLASK_ENV"] = "production"
    import app as flask_app
    flask_app.app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def start_tunnel():
    """Wait for Flask to start then open ngrok tunnel."""
    time.sleep(2)  # Give Flask time to boot
    
    try:
        from pyngrok import ngrok, conf
        
        # Optional: if you have an authtoken, set it here for longer sessions
        # ngrok.set_auth_token("YOUR_NGROK_AUTHTOKEN")
        
        # Create HTTP tunnel on port 5000
        tunnel = ngrok.connect(5000, "http")
        public_url = tunnel.public_url
        
        print("\n" + "=" * 60)
        print("  ██╗     ███████╗██╗  ██╗ █████╗ ██╗   ██╗██████╗ ██╗████████╗")
        print("  ██║     ██╔════╝╚██╗██╔╝██╔══██╗██║   ██║██╔══██╗██║╚══██╔══╝")
        print("  ██║     █████╗   ╚███╔╝ ███████║██║   ██║██║  ██║██║   ██║   ")
        print("  ██║     ██╔══╝   ██╔██╗ ██╔══██║██║   ██║██║  ██║██║   ██║   ")
        print("  ███████╗███████╗██╔╝ ██╗██║  ██║╚██████╔╝██████╔╝██║   ██║   ")
        print("  ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ")
        print("=" * 60)
        print(f"\n  ✅  LOCAL  : http://127.0.0.1:5000")
        print(f"  🌐  LIVE   : {public_url}")
        print(f"\n  Share the LIVE link above with anyone on the internet!")
        print(f"  Press Ctrl+C to stop both the server and tunnel.\n")
        print("=" * 60 + "\n")
        
        # Keep the tunnel alive
        ngrok_process = ngrok.get_ngrok_process()
        try:
            ngrok_process.proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down tunnel and server...")
            ngrok.kill()
            
    except Exception as e:
        print(f"\n[ERROR] Could not create ngrok tunnel: {e}")
        print("  → The app is still running locally at http://127.0.0.1:5000")
        print("  → To get a public URL, sign up free at https://ngrok.com and run:")
        print("    ngrok http 5000\n")


if __name__ == "__main__":
    print("\nStarting LEXAUDIT server and ngrok tunnel...")
    
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Start ngrok tunnel (blocking, in main thread)
    start_tunnel()
