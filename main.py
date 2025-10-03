import os
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path
import sys

def firstsetup():
    # --- Check for root ---
    if os.geteuid() != 0:
        print("❌ This script must be run as root. Exiting.")
        sys.exit(1)

    try:
        # Step 1: Install required packages
        subprocess.run(
            ["apt-get", "install", "-y", "git", "ffmpeg", "gpac", "golang-go", "wget"],
            check=True
        )
        print("✅ Packages installed successfully!")

        # Step 2: Download and set up Bento4
        HOME = Path.home()
        INSTALL_DIR = HOME / "bento4"
        BASHRC = HOME / ".bashrc"
        BENTO4_URL = "https://github.com/axiomatic-systems/Bento4/releases/download/v1.6.0-639/Bento4-SDK-1-6-0-639.x86_64-unknown-linux.zip"

        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = INSTALL_DIR / "bento4.zip"

        print(f"⬇️ Downloading Bento4 from {BENTO4_URL}...")
        urllib.request.urlretrieve(BENTO4_URL, zip_path)
        print("Extracting Bento4...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(INSTALL_DIR)
        os.remove(zip_path)

        extracted_dirs = [d for d in INSTALL_DIR.iterdir() if d.is_dir()]
        if not extracted_dirs:
            raise RuntimeError("❌ No extracted folder found in ~/bento4")
        
        bin_dir = extracted_dirs[0] / "bin"
        export_line = f'export PATH="{bin_dir}:$PATH"\n'

        if export_line not in BASHRC.read_text():
            with open(BASHRC, "a") as f:
                f.write("\n# Added by Bento4 installer\n")
                f.write(export_line)
            print(f"✅ Added Bento4 bin to PATH in {BASHRC}")
        else:
            print("ℹ️ Bento4 bin already in PATH")

        # Step 3: Download and extract wrapper
        WRAPPER_URL = "https://github.com/zhaarey/wrapper/releases/download/linux.V2/wrapper.x86_64.tar.gz"
        WRAPPER_DIR = HOME / "wrapper"
        WRAPPER_TAR = HOME / "wrapper.x86_64.tar.gz"

        print(f"⬇️ Downloading wrapper from {WRAPPER_URL}...")
        urllib.request.urlretrieve(WRAPPER_URL, WRAPPER_TAR)
        print("Extracting wrapper...")

        WRAPPER_DIR.mkdir(parents=True, exist_ok=True)
        with tarfile.open(WRAPPER_TAR, "r:gz") as tar:
            tar.extractall(WRAPPER_DIR)
        os.remove(WRAPPER_TAR)

        print("✅ Wrapper extracted to ~/wrapper")

        # Step 4: Clone Apple Music Downloader repo
        AMD_DIR = HOME / "apple-music-downloader"
        if not AMD_DIR.exists():
            print("⬇️ Cloning Apple Music Downloader...")
            subprocess.run(
                ["git", "clone", "https://github.com/zhaarey/apple-music-downloader", str(AMD_DIR)],
                check=True
            )
            print("✅ Apple Music Downloader cloned into ~/apple-music-downloader")
        else:
            print("ℹ️ Apple Music Downloader already exists, skipping clone")

        print("🎉 First setup complete! Run this to reload PATH:")
        print(f"    source {BASHRC}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed during setup: {e}")
        sys.exit(1)

def start():
    print("🚀 Starting Apple Music Downloader Web UI...")
    
    # Import and run the Flask app
    from app.app import app
    
    # Start the web server
    app.run(host='0.0.0.0', port=5000, debug=True)

# === First run check ===
script_dir = os.path.dirname(os.path.abspath(__file__))
marker_file = os.path.join(script_dir, "firstrun")

if not os.path.exists(marker_file):
    firstsetup()
    with open(marker_file, "w") as f:
        f.write("This file marks that first setup has been completed.\n")
else:
    start()
