import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-pro-002')

# Configure ElevenLabs API
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Hardcoded question
HARDCODED_QUESTION = """
                    Generate a podcast script based on the following PDF file. 
                    There must only be one male podcast host and zero guests. 
                    Do not include any sound effects. Do not include music. Do not include any other types of effects to the script.
                    Give me the script without any formatting. i.e. do not include Host: or Guest: headers or (starts/ends)
                    """

def process_pdf(uploaded_file):
    # Save the uploaded file temporarily
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # Upload the file to Google's API
    sample_file = genai.upload_file(path="temp.pdf", display_name="Uploaded PDF")
    
    # Generate content using the model with the hardcoded question
    response = model.generate_content([sample_file, HARDCODED_QUESTION], stream=True)
    
    # Remove the temporary file
    os.remove("temp.pdf")
    
    return response

def text_to_speech_file(text: str) -> str:
    # Calling the text_to_speech conversion API with detailed parameters
    response = elevenlabs_client.text_to_speech.convert(
        voice_id=selected_voice_key,  # get the key from the voice_options dictionary
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",  # use the turbo model for low latency
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Generating a unique file name for the output MP3 file
    save_file_path = f"{uuid.uuid4()}.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    # Return the path of the saved audio file
    return save_file_path

# Streamlit app
st.title("Podcast Generator")

# Get user input (optional)
user_input = st.text_area("Add on any specific tone or instructions.", placeholder="E.g. 'Slightly weird and wonky!' or 'Serious TED Talks style'")

if st.button("Save"):
    st.session_state['saved_input'] = user_input
    st.success("Input saved successfully!")

# Retrieve saved input if available
saved_input = st.session_state.get('saved_input', '')

# Concatenate user input to the hardcoded question if provided
if user_input:
    HARDCODED_QUESTION += "\n" + user_input

# Create a dropdown for user to select a voice
voice_options = {
    "Sarah (American, soft, news)": "EXAVITQu4vr4xnSDxMaL",
    "Laura (American, upbeat, social media)": "FGY2WhTYpPnrIDTdsKH5",
    "Charlie (Australian, natural, conversational)": "IKne3meq5aSn9XLyUdCD",
    "George (British, warm, narration)": "JBFqnCBsd6RMkjVDRZzb",
    "Callum (Transatlantic, intense, characters)": "N2lVS1w4EtoT3dr4eOWO",
    "River (American, confident, social media)": "SAz9YHcvj6GT2YYXdXww",
    "Liam (American, friendly, conversational)": "TX3LPaxmHKxFdv7VOQHJ",
    "Chris (American, casual, conversational)": "iP95p4xoKVk53GoZ742B",
    "Brian (American, deep, narration)": "nPczCjzI2devNBz1zQrb",
    "Daniel (British, authoritative, news)": "onwK4e9ZLuTAKqWW03F9",
    "Lily (British, warm, narration)": "pFZP5JQG7iQjIQuC4Bku",
    "Bill (American, trustworthy, narration)": "pqHfZKP75CvOlQylNhV4"
}

selected_voice = st.selectbox("Select a voice for the podcast:", options=list(voice_options.keys()))

# Get the key of the selected voice
selected_voice_key = voice_options[selected_voice]

# File uploader
uploaded_file = st.file_uploader("", type="pdf")

if uploaded_file is not None:
    if st.button("Execute Process"):
        with st.spinner("Processing..."):
            response = process_pdf(uploaded_file)
            
            # Create a placeholder for the streaming output
            output_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    output_placeholder.markdown(full_response)
            
            # Generate audio from the text
            audio_file_path = text_to_speech_file(full_response)
            
            # Display audio player
            st.audio(audio_file_path)
            
            # Provide download link for the audio file
            with open(audio_file_path, "rb") as file:
                st.download_button(
                    label="Download Podcast Audio",
                    data=file,
                    file_name="podcast.mp3",
                    mime="audio/mpeg"
                )
            
            # Clean up the audio file after processing
            os.remove(audio_file_path)
else:
    st.write("Start by uploading a PDF file as content for your podcast.")
