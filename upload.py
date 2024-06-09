import requests
import os
import shutil
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

# Load environment variables
load_dotenv()

client = OpenAI()
# Set your OpenAI API key
client.api_key = os.getenv('OPENAI_API_KEY')

# Function to generate random facts and interesting texts based on a topic
def generate_facts(topic):
    prompt = f"Generate 10 random interesting facts about {topic} and making it long."
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=500
    )
    facts = response.choices[0].text.strip().split('\n')
    return facts

# Function to generate an image query based on a topic
def TTIQ(topic):
    prompt = f"Generate an image query for dall-e based on {topic}."
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=500
    )
    imgQ = response.choices[0].text.strip()
    return imgQ

# Function to generate an image based on a prompt
def generate_image(prompt):
    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    return image_url

# Function to download an image from a URL
def download_image(url, filename):
    image_data = requests.get(url).content
    with open(filename, 'wb') as handler:
        handler.write(image_data)

# Function to convert text to speech using OpenAI TTS and save as an MP3 file
def text_to_speech(text, filename):
    speech_file_path = Path(__file__).parent / filename
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )
    response.stream_to_file(speech_file_path)

# Function to animate images with text
def create_image_clips(images, facts):
    clips = []
    for i, (image, fact) in enumerate(zip(images, facts)):
        image_clip = ImageClip(image).set_duration(5)
        text_clip = TextClip(fact, fontsize=24, color='white', size=(500, 150)).set_position('bottom').set_duration(5)
        video = CompositeVideoClip([image_clip, text_clip])
        clips.append(video)
    return clips

# Main function to create a video
def create_video(topic):
    images_dir = './images'
    
    # Create the images directory if it doesn't exist
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    try:
        # Step 1: Generate random facts based on the topic
        facts = generate_facts(topic)
        print(f"Facts Generated:")

        # Step 2: Generate images related to the topic
        images = []
        for i in range(5):
            image_prompt = f"{topic} fact {i+1}: {facts[i]}"
            topic_to_image_query = TTIQ(image_prompt)
            image_url = generate_image(topic_to_image_query)
            #show progress
            print(f"{i+1} st image generated")
            image_filename = os.path.join(images_dir, f'generated_image_{i+1}.jpg')
            download_image(image_url, image_filename)
            images.append(image_filename)

        # Step 3: Convert the script (facts) to speech
        script_text = ' '.join(facts)
        text_to_speech(script_text, 'audio.mp3')

        # Step 4: Create video clips with animated images and facts
        clips = create_image_clips(images, facts)
        final_clip = concatenate_videoclips(clips, method="compose")

        # Step 5: Add audio to the video
        audio_clip = AudioFileClip('audio.mp3')
        final_video = final_clip.set_audio(audio_clip)

        # Export the final video
        final_video.write_videofile(f"{topic}.mp4", codec= "libx264", fps=24, ffmpeg_params=["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"])
    
    finally:
        # Remove the images directory after the process
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
        # Remove the audio file
        if os.path.exists('audio.mp3'):
            os.remove('audio.mp3')

# Define the topic
topic = "Roman Empire"

# Run the video creation process
create_video(topic)