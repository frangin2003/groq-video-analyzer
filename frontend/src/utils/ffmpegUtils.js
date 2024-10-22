const ffmpeg = require('ffmpeg-static');
const { execFile } = require('child_process');
const { promisify } = require('util');
const path = require('path');

const execFileAsync = promisify(execFile);

async function extractFrames(videoPath, outputDir, frameRate = 1) {
  const outputPath = path.join(outputDir, 'frame_%d.jpg');
  
  try {
    await execFileAsync(ffmpeg, [
      '-i', videoPath,
      '-vf', `fps=${frameRate}`,
      '-q:v', '2',
      outputPath
    ]);
    console.log('Frames extracted successfully');
  } catch (error) {
    console.error('Error extracting frames:', error);
    throw error;
  }
}

module.exports = {
  extractFrames
};