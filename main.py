import os
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent
BENTO4_DIR = PROJECT_DIR / "bento4"
WRAPPER_DIR = PROJECT_DIR / "wrapper"
AMD_DIR = PROJECT_DIR / "apple-music-downloader"

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
        BENTO4_URL = "https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip"
        zip_path = PROJECT_DIR / "bento4.zip"

        if not BENTO4_DIR.exists():
            print(f"⬇️ Downloading Bento4 from {BENTO4_URL}...")
            urllib.request.urlretrieve(BENTO4_URL, zip_path)
            print("Extracting Bento4...")

            BENTO4_DIR.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(BENTO4_DIR)
            os.remove(zip_path)

            print("✅ Bento4 installed inside project folder")
        else:
            print("ℹ️ Bento4 already exists, skipping download")

        # Step 3: Download and extract wrapper
        WRAPPER_URL = "https://github.com/zhaarey/wrapper/releases/download/linux.V2/wrapper.x86_64.tar.gz"
        wrapper_tar = PROJECT_DIR / "wrapper.x86_64.tar.gz"

        if not WRAPPER_DIR.exists():
            print(f"⬇️ Downloading wrapper from {WRAPPER_URL}...")
            urllib.request.urlretrieve(WRAPPER_URL, wrapper_tar)
            print("Extracting wrapper...")

            WRAPPER_DIR.mkdir(parents=True, exist_ok=True)
            with tarfile.open(wrapper_tar, "r:gz") as tar:
                tar.extractall(WRAPPER_DIR)
            os.remove(wrapper_tar)

            print("✅ Wrapper extracted inside project folder")
        else:
            print("ℹ️ Wrapper already exists, skipping download")

        # Step 4: Clone Apple Music Downloader repo
        if not AMD_DIR.exists():
            print("⬇️ Cloning Apple Music Downloader...")
            subprocess.run(
                ["git", "clone", "https://github.com/zhaarey/apple-music-downloader", str(AMD_DIR)],
                check=True
            )
            print("✅ Apple Music Downloader cloned inside project folder")
        else:
            print("ℹ️ Apple Music Downloader already exists, skipping clone")

        print("🎉 First setup complete!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed during setup: {e}")
        sys.exit(1)

def start():
    print("🚀 Starting Apple Music Downloader Web UI...")

    # Ensure Bento4 and Wrapper are in PATH locally
    bin_candidates = list(BENTO4_DIR.glob("Bento4*"))  # find extracted folder
    if bin_candidates:
        bin_dir = bin_candidates[0] / "bin"
        os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"

    os.environ["PATH"] = f"{WRAPPER_DIR}:{os.environ['PATH']}"

    # Import and run the Flask app
    from app import app   # FIXED: no double "app.app"
    app.run(host="0.0.0.0", port=5000, debug=True)

# === First run check ===
marker_file = PROJECT_DIR / "firstrun"

if not marker_file.exists():
    firstsetup()
    with open(marker_file, "w") as f:
        f.write("This file marks that first setup has been completed.\n")

start()
