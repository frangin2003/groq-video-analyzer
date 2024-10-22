import { OpenAI } from 'langchain/llms/openai';
import { OpenAIEmbeddings } from 'langchain/embeddings/openai';
import ffmpeg from 'ffmpeg-static';
import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';

const openai = new OpenAI({ temperature: 0 });
const embeddings = new OpenAIEmbeddings();

export async function extractFrames(videoPath, outputDir, frameInterval) {
  return new Promise((resolve, reject) => {
    const command = `${ffmpeg} -i "${videoPath}" -vf "select='not(mod(n,${frameInterval}))'" -vsync vfr "${path.join(outputDir, 'frame%d.png')}"`;
    exec(command, (error, stdout, stderr) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

export async function analyzeFrame(imagePath) {
  const prompt = `You are Image Analyzer GPT, an advanced AI model specialized in extracting rich, detailed metadata from images. Your task is to analyze the given image and provide a comprehensive description that captures all relevant details. This description should be suitable for use in a vector database to enable accurate similarity searches for image sequences.

When analyzing an image, focus on the following aspects:

Overall scene: Describe the general setting and atmosphere (e.g., urban landscape, natural environment, indoor scene).
Specific location: If identifiable, mention any landmarks, place names, or recognizable locations.
Main subjects: Identify and describe the primary focus of the image (e.g., people, animals, objects, buildings).
Actions and interactions: Detail any activities or interactions occurring in the image (e.g., people walking, animals feeding, vehicles moving).
Visual composition: Describe the layout, perspective, and prominent visual elements.
Environmental factors: Note weather conditions, time of day, and lighting characteristics.
Colors and textures: Highlight dominant colors, patterns, and textures in the image.
Emotional tone: If applicable, describe the mood or atmosphere conveyed by the image.
Temporal indicators: Mention any elements that suggest a specific time period or era.
Quantities: Provide approximate numbers for countable elements in the scene.
Details and nuances: Include small but potentially significant details that contribute to the overall scene.

Your description should be a single, coherent paragraph that flows naturally while incorporating all relevant information. Aim for a balance between brevity and detail, ensuring that the description is comprehensive enough for accurate similarity searches without becoming excessively verbose.`;

  const imageData = fs.readFileSync(imagePath, { encoding: 'base64' });
  const response = await openai.call(prompt, { image: imageData });
  return response;
}

export async function createEmbedding(text) {
  const embedding = await embeddings.embedQuery(text);
  return embedding;
}

// Implement vector database functions here
// For example, using a library like hnswlib-node for local vector storage

let vectorStore = [];

export function addToVectorStore(videoFileName, timestampMilliseconds, frameNumber, description, embedding) {
  vectorStore.push({
    video_file_name: videoFileName,
    timestamp_milliseconds: timestampMilliseconds,
    frame_number: frameNumber,
    description: description,
    embedding: embedding,
  });
}

export function searchVectorStore(queryEmbedding, limit = 10) {
  // Implement cosine similarity search
  const results = vectorStore
    .map(item => ({
      ...item,
      similarity: cosineSimilarity(queryEmbedding, item.embedding),
    }))
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit);

  return results;
}

function cosineSimilarity(a, b) {
  const dotProduct = a.reduce((sum, _, i) => sum + a[i] * b[i], 0);
  const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
  const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
  return dotProduct / (magnitudeA * magnitudeB);
}