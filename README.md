# groq-video-analyzer
Find and extract video sequences with just your words!

This app allows you to scan folders and video files, automatically extracting frames from each file, describing them using generative AI, and storing them as embeddings in a local vector database. You can then perform natural language searches to find specific sequences across all indexed videos. A sequence is a subset of a video, and a video can contain none or many sequences corresponding to the search.

<ul>
<li>📂 Scan folders and videos to extract frames, describe them with AI, and store them in a local database.</li>
<li>🔍 Perform natural language searches to find specific sequences across all indexed videos.</li>
<li>🎬 Extract and utilize video sequences based on your search results.</li>
</ul>

# Stack
TypeScript, JavaScript, React, TailwindCSS, FastAPI, Groq, Pinecone, Replit

# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)


## Backend

To run the backend, run `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload` at the root directory.


## Video Attributions
https://commons.wikimedia.org/wiki/File:Steamboat_Willie_(1928)_by_Walt_Disney.webm
https://commons.wikimedia.org/wiki/File:Why_Many_Cities_Suck_(but_Dutch_Cities_Don%27t).webm
https://commons.wikimedia.org/wiki/File:San_Francisco_Downtown_Driving_Tour,_2023_California,_USA._Travel_Guide,_(4K_HDR).webm
https://commons.wikimedia.org/wiki/File:D%C3%A4nemark_Teil_2_-_mit_dem_E-Bike_nach_Kopenhagen_-_Puttgarden_-_Faxe.webm
https://commons.wikimedia.org/wiki/File:33_minutes_Paris,_France,_drone.webm
https://commons.wikimedia.org/wiki/File:Aerial_views_of_World_Trade_Center,_Freedom_Tower,_Battery_Park_City,_Downtown_Manhattan,_Hudson_River,_Westside_Highway,_New_York_City,_USA.webm