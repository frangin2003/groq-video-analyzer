# groq-video-analyzer
Find and extract video sequences with just your words! 🎥✨

This app allows you to analyze video files, automatically extracting frames eery 2 seconds, describing them using generative AI, and storing them as embeddings in a local vector database. You can then perform natural language searches to find specific sequences across all indexed videos. A sequence is a subset of a video, and a video can contain none or many sequences corresponding to the search.

<ul>
<li>📂 Scan folders and videos to extract frames, describe them with AI, and store them in a local database.</li>
<li>🔍 Perform natural language searches to find specific sequences across all indexed videos.</li>
<li>🎬 Extract and utilize video sequences based on your search results.</li>
</ul>

## Local Installation Steps 🚀

### Prerequisites 📋

1. **Ollama** 🦙
   - Download and install Ollama from the official repository: [Ollama Download](https://ollama.com/download) 📥

2. **Conda (that will install Python)** 🐍
   - Download and install Conda from the official website: [Conda Installation Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) 📥


3. **Node.js and npm** 🌐
   - You need to install Node.js and npm to install dependencies. Download and install Node.js from the official website: [Node.js Download](https://nodejs.org/en/download/package-manager) 📥
   - Verify the installation by running:
     ```sh
     node -v
     npm -v
     ```
### Commands/Steps 🛠️

1. **Run Ollama Models (Only first time to download the models)** 🦙
   - Run the Ollama LLaVa model (vision LLM for image description generation):
     ```sh
     ollama run llava
     ```
     Then `/bye` to exit 👋
   - Pull the mxbai-embed-large model (for embedding frames):
     ```sh
     ollama pull mxbai-embed-large
     ```
     Then `/bye` to exit 👋


2. **Install (and eventually build) the Frontend** 🏗️
   - Navigate to the frontend directory:
     ```sh
     cd frontend
     ```
   - Install the required npm packages:
     ```sh
     npm install
     ```
   - Build the frontend for production (Optional since the build is already included in the repo):
     ```sh
     npm run build
     ```
   - The build output will be in the `build` folder.

3. **Create Conda Environment** 🐍
   - Create a new Conda environment for Python 3.10 named `groq-video-analyzer` (only first time):
     ```sh
     conda create -n groq-video-analyzer python=3.10
     ```
   - Activate the environment:
     ```sh
     conda activate groq-video-analyzer
     ```

4. **Install Python Requirements** 📦
   - Install the required Python packages (only first time):
     ```sh
     pip install -r requirements.txt
     ```

5. **Start the Application** ▶️
   - Run the following command to start the application:
     ```sh
     python main_local.py
     ```

6. **Access the Application** 🌐
   - Open your web browser and navigate to:
     [http://localhost:8000/](http://localhost:8000/)


# 🗂️ Stack
## 🌐 Replit Stack
🟦 JavaScript, ⚛️ React, 🎨 TailwindCSS, 🚀 FastAPI, 🐍 Python, 🌟 Uvicorn, 🧠 Groq, 🌲 Pinecone, 🌀 Replit

## 🖥️ Local Stack
🟦 JavaScript, ⚛️ React, 🎨 TailwindCSS, 🚀 FastAPI, 🐍 Python, 🌟 Uvicorn, 🧠 Ollama, 🦙 Llama3.2, 🦙 Llava1.6

# 🛠️ Development

## 🦙 Ollama
📚 Ollama API docs: https://github.com/ollama/ollama/blob/main/docs/api.md

- List available models: `http://localhost:11434/api/tags`
- List running models: `http://localhost:11434/api/ps`

## React commands
- ▶️ Start: `npm start`
- 🏗️ Build: `npm run build` (Builds the app for production to the `build` folder)

## Python Backend

To run the backend, run `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload` at the root directory.

# Credits
## 🎥 Video Attributions
- https://commons.wikimedia.org/wiki/File:Steamboat_Willie_(1928)_by_Walt_Disney.webm
- https://commons.wikimedia.org/wiki/File:Why_Many_Cities_Suck_(but_Dutch_Cities_Don%27t).webm
- https://commons.wikimedia.org/wiki/File:San_Francisco_Downtown_Driving_Tour,_2023_California,_USA._Travel_Guide,_(4K_HDR).webm
- https://commons.wikimedia.org/wiki/File:D%C3%A4nemark_Teil_2_-_mit_dem_E-Bike_nach_Kopenhagen_-_Puttgarden_-_Faxe.webm
- https://commons.wikimedia.org/wiki/File:33_minutes_Paris,_France,_drone.webm
- https://commons.wikimedia.org/wiki/File:Aerial_views_of_World_Trade_Center,_Freedom_Tower,_Battery_Park_City,_Downtown_Manhattan,_Hudson_River,_Westside_Highway,_New_York_City,_USA.webm