import sys
import os

# Add the parent directory to the path so it can find your env.py file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """
    This is the entry point required by the OpenEnv multi-mode validator.
    It simply triggers the standard OpenEnv web server.
    """
    print("🚀 Booting OpenEnv Multi-Mode Server...")
    os.system("openenv serve --host 0.0.0.0 --port 7860")

if __name__ == "__main__":
    main()