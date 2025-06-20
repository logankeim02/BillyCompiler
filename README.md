Video Compiler
This application is a desktop tool built with PyQt6 that allows you to easily compile multiple video clips into a single, cohesive video. It provides options to customize the total video length, individual clip durations, video layout (single clip or grid layouts like 2x2, 3x3), and audio volume for the compilation. It leverages the power of FFmpeg for all video processing tasks.

✨ Features
Batch Video Compilation: Select a folder containing your video clips, and the application will combine them.

Customizable Output Length: Define the desired total duration of your compiled video.

Flexible Clip Lengths: Set the duration for each individual scene/clip within the compilation.

Dynamic Layout Mixing: Choose between a single video layout or various grid layouts (2x2, 3x3) for different scenes, with a configurable mix percentage.

Audio Control: Adjust the volume of the audio from the source clips.

Real-time Progress: Monitor the video generation process with a progress bar and detailed FFmpeg logs.

Intuitive UI: A user-friendly graphical interface powered by PyQt6.

📝 Prerequisites
Before running this application, you need to install the following software:

Python 3.x: The programming language the application is written in.

FFmpeg: A powerful command-line tool for video and audio processing. This application relies heavily on FFmpeg and ffprobe (which comes with FFmpeg) being installed and accessible in your system's PATH.

PyQt6: A set of Python bindings for the Qt application framework, used for the graphical user interface.

yt-dlp (Optional but Recommended): While not directly used by this specific code, yt-dlp is a popular tool for downloading videos and audio from various websites, which can be a great source for clips to use with this compiler. The user explicitly requested instructions for this, so it's included as a useful companion tool.

🛠️ Installation Guide
Follow these steps to set up your environment and run the Video Compiler.

Step 1: Install Python
If you don't have Python installed, download it from the official website.

Download Python: Visit python.org

Installation:

Windows: During installation, make sure to check the box that says "Add Python to PATH". This is crucial for running Python commands from the command line.

macOS/Linux: Python is often pre-installed. You can verify by opening a terminal and typing python3 --version. If not present or if you need a newer version, use a package manager (like Homebrew for macOS or apt/yum for Linux) or download from the official site.

After installation, verify Python and pip (Python's package installer) are working by opening a new terminal or command prompt and typing:

python3 --version
pip3 --version

(On some systems, python and pip might be used instead of python3 and pip3.)

Step 2: Install FFmpeg
FFmpeg is essential for video processing. You must ensure ffmpeg and ffprobe are in your system's PATH.

Download FFmpeg: Visit the official FFmpeg download page: ffmpeg.org/download.html

Installation Instructions by Operating System:
Windows:

Download: Go to ffmpeg.org/download.html, click the Windows icon, and then choose a reputable build (e.g., gyan.dev or btbn.org). Download the zip file.

Extract: Extract the downloaded zip file to a stable location on your computer (e.g., C:\ffmpeg). You should see folders like bin, doc, licenses inside.

Add to PATH (Crucial Step):

Right-click the Start button and select System.

Click Advanced system settings on the right (or search for it).

Click Environment Variables....

Under System variables, find the Path variable and select it. Click Edit....

Click New and add the path to the bin folder inside your FFmpeg extraction (e.g., C:\ffmpeg\bin).

Click OK on all windows to close them.

Verify: Open a new Command Prompt or PowerShell window (existing ones might not pick up the new PATH) and type:

ffmpeg -version
ffprobe -version

You should see version information for both.

macOS:

Using Homebrew (Recommended):

If you don't have Homebrew, install it by following instructions on brew.sh.

Open Terminal and run:

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Once Homebrew is installed, install FFmpeg:

brew install ffmpeg

Verify: Open a new Terminal window and type:

ffmpeg -version
ffprobe -version

You should see version information for both.

Linux (Debian/Ubuntu):

Open Terminal and run:

sudo apt update
sudo apt install ffmpeg

Verify: Open a new Terminal window and type:

ffmpeg -version
ffprobe -version

You should see version information for both.

Step 3: Install PyQt6
Open your terminal or command prompt and run:

pip3 install PyQt6

(Use pip install PyQt6 if pip3 doesn't work).

Step 4: Install yt-dlp (Optional but Recommended)
yt-dlp is a command-line program to download videos from YouTube and many other video sites. It's a great way to acquire source videos for your compilations.

Open your terminal or command prompt and run:

pip3 install yt-dlp

(Use pip install yt-dlp if pip3 doesn't work).

🚀 How to Run the Application
Download the Code: Get the video_compiler.py file (or whatever you named the script) onto your computer.

Open Terminal/Command Prompt: Navigate to the directory where you saved the Python script using the cd command. For example:

cd path/to/your/folder

Run the Script: Execute the Python script:

python3 video_compiler.py

(Use python video_compiler.py if python3 doesn't work).

The Video Compiler application window should appear.

🖥️ Using the Application
1. Sources:

Select Source Folder (Recursive): Click this button to choose a directory containing your video files (.mp4, .mov, .avi, .mkv). The application will recursively scan all subfolders for supported video files. The label below will show how many videos were found.

2. Output & Layout:

Total Video Length: Set the desired final duration of your compiled video in seconds.

Clip Length: Define how long each individual scene/clip should last in seconds.

Layout Mix (Single Clips <-> Grids): Use the slider to control the probability of grid layouts appearing. A value of 0% means only single-clip layouts will be used. A value of 100% means only 2x2 or 3x3 grids will be used (if enough source videos are available).

Select Destination Folder: Choose where the final compiled video will be saved.

Output Filename: Enter the desired name for your output video file (e.g., compilation.mp4).

3. Audio:

Clip Audio Volume: Adjust the volume of the audio tracks from the source clips. This is a percentage, where 100% is original volume.

Generate Video: Once all settings are configured, click this button to start the video compilation process.

Status Label & Progress Bar: Monitor the progress and current task.

FFmpeg Log: A text area will display the detailed output from FFmpeg, which can be useful for debugging.

Completion: Upon successful completion, a message box will appear, and the output folder will automatically open. If an error occurs, an error message will be displayed in the log and a critical message box will pop up.

🛑 Troubleshooting
"FFmpeg and FFprobe Not Found" Warning: This is the most common issue. It means FFmpeg is either not installed or not correctly added to your system's PATH. Refer to the "Install FFmpeg" section above and ensure you restart your terminal/command prompt after modifying the PATH.

"Please select a source folder." Error: You must select a folder containing video files before clicking "Generate Video".

Compilation Fails/Errors in Log:

Check the FFmpeg Log box for specific error messages.

Ensure your source video files are not corrupted.

Verify you have enough disk space in your destination folder.

If generating large videos or complex grids, ensure your system has sufficient RAM and CPU resources.

Video Playback Issues: If the generated video plays incorrectly, try a different Output Filename with a common extension like .mp4. Ensure your media player supports the H.264 codec.

🤝 Contribution
Feel free to fork this repository, suggest improvements, or submit pull requests.

📄 License
This project is open-source and available under the MIT License.
