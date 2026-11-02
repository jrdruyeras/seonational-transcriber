import streamlit as st
import os
import json
from faster_whisper import WhisperModel

# Page Configuration & Branding
st.set_page_config(
    page_title="SEO National Local Transcriber Studio",
    page_icon="🎙️",
    layout="wide"
)

st.title("SEO National Local Transcriber Studio")
st.markdown("*Created by Rego* | Professional Audio & Video Transcription Web Studio")
st.divider()

# Sidebar Settings
st.sidebar.header("Transcription Settings")
model_size = st.sidebar.selectbox("Select Whisper Model Size", ["tiny", "base", "small", "medium"], index=1)
clean_fillers = st.sidebar.checkbox("Remove Filler Words (um, uh, you know)", value=True)

# Main File Uploader
uploaded_file = st.file_uploader("Upload Audio or Video File", type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "m4a"])

if uploaded_file is not None:
    # Save uploaded file temporarily to process
    temp_file_path = os.path.join(".", uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.audio(temp_file_path)
    
    if st.button("Start Transcription", type="primary"):
        with st.spinner("Processing audio and extracting timestamps..."):
            try:
                # Load Whisper model locally on the server
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                segments, info = model.transcribe(temp_file_path, beam_size=5, word_timestamps=True)
                
                structured_segments = []
                speaker_toggle = True
                
                for seg in segments:
                    text = seg.text.strip()
                    if not text:
                        continue
                    
                    if clean_fillers:
                        for f in [" um ", " uh ", " er ", " ah ", " you know "]:
                            text = text.replace(f, " ")
                    
                    speaker_id = "Host" if speaker_toggle else "Guest"
                    if seg.end - seg.start > 5.0:
                        speaker_toggle = not speaker_toggle

                    structured_segments.append({
                        "start": seg.start,
                        "end": seg.end,
                        "speaker": speaker_id,
                        "text": text.strip()
                    })

                st.session_state["transcript"] = structured_segments
                st.success("Transcription complete!")
            except Exception as e:
                st.error(f"Error during transcription: {str(e)}")

# Display Workspace if transcript exists
if "transcript" in st.session_state and st.session_state["transcript"]:
    st.divider()
    st.subheader("Transcript Workspace & Editor")
    
    # Editable transcript view
    transcript_text_lines = []
    for seg in st.session_state["transcript"]:
        hours = int(seg["start"] // 3600)
        minutes = int((seg["start"] % 3600) // 60)
        secs = int(seg["start"] % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        transcript_text_lines.append(f"[{time_str}] {seg['speaker']}: {seg['text']}")

    edited_transcript = st.text_area("Edit Transcript Below:", value="\n\n".join(transcript_text_lines), height=300)

    # Export Options
    st.subheader("Export Center")
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Download as TXT",
            data=edited_transcript,
            file_name="transcript.txt",
            mime="text/plain"
        )
        
    with col2:
        json_data = json.dumps({
            "application": "SEO National Local Transcriber Studio",
            "creator": "Rego",
            "segments": st.session_state["transcript"]
        }, indent=4)
        
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name="transcript.json",
            mime="application/json"
        )