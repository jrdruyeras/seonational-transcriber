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
model_size = st.sidebar.selectbox("Select Whisper Model Size", ["tiny", "base", "small", "medium", "large-v3"], index=1)
clean_fillers = st.sidebar.checkbox("Remove Filler Words (um, uh, you know)", value=True)

# Initialize Session State for Speakers and Transcript
if "speaker_names" not in st.session_state:
    st.session_state["speaker_names"] = {"SPEAKER_01": "Host", "SPEAKER_02": "Guest"}

# Main File Uploader
uploaded_file = st.file_uploader("Upload Audio or Video File", type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "m4a"])

if uploaded_file is not None:
    temp_file_path = os.path.join(".", uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.audio(temp_file_path)
    
    if st.button("Start Transcription", type="primary"):
        with st.spinner(f"Processing audio with Whisper model ('{model_size}')... This may take a moment."):
            try:
                # Load Whisper model on cloud server (CPU)
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
                    
                    speaker_id = "SPEAKER_01" if speaker_toggle else "SPEAKER_02"
                    if seg.end - seg.start > 5.0:
                        speaker_toggle = not speaker_toggle

                    words_data = []
                    if hasattr(seg, 'words') and seg.words:
                        for w in seg.words:
                            words_data.append({
                                "word": w.word.strip(),
                                "start": w.start,
                                "end": w.end
                            })

                    structured_segments.append({
                        "start": seg.start,
                        "end": seg.end,
                        "speaker": speaker_id,
                        "text": text.strip(),
                        "words": words_data
                    })

                st.session_state["transcript"] = structured_segments
                st.success("Transcription complete!")
            except Exception as e:
                st.error(f"Error during transcription: {str(e)}")

# Display Workspace if transcript exists
if "transcript" in st.session_state and st.session_state["transcript"]:
    st.divider()
    st.subheader("Transcript Workspace & Editor")
    
    # Speaker Renaming Section in Sidebar
    st.sidebar.divider()
    st.sidebar.subheader("Speaker Management")
    for s_key in st.session_state["speaker_names"]:
        current_name = st.session_state["speaker_names"][s_key]
        new_name = st.sidebar.text_input(f"Rename {s_key}", value=current_name)
        st.session_state["speaker_names"][s_key] = new_name

    # Find & Replace tools
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        find_word = st.text_input("Find word/phrase:")
    with col_f2:
        replace_word = st.text_input("Replace with:")
    
    if st.button("Apply Find & Replace"):
        if find_word:
            for seg in st.session_state["transcript"]:
                seg["text"] = seg["text"].replace(find_word, replace_word)
            st.success(f"Replaced all instances of '{find_word}' with '{replace_word}'!")

    # Helper formatting function
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    # Build editable view
    transcript_text_lines = []
    for seg in st.session_state["transcript"]:
        time_str = format_time(seg["start"])
        speaker_name = st.session_state["speaker_names"].get(seg["speaker"], seg["speaker"])
        transcript_text_lines.append(f"[{time_str}] {speaker_name}: {seg['text']}")

    edited_transcript = st.text_area("Edit Transcript Below:", value="\n\n".join(transcript_text_lines), height=350)

    # Export Center
    st.divider()
    st.subheader("Export Center")
    
    include_timestamps = st.checkbox("Include Timestamps in Export", value=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # TXT Export
        export_txt_lines = []
        for seg in st.session_state["transcript"]:
            ts = f"[{format_time(seg['start'])}] " if include_timestamps else ""
            name = st.session_state["speaker_names"].get(seg["speaker"], seg["speaker"])
            export_txt_lines.append(f"{ts}{name}: {seg['text']}")
        
        st.download_button(
            label="Download as TXT",
            data="\n\n".join(export_txt_lines),
            file_name="transcript.txt",
            mime="text/plain"
        )
        
    with col2:
        # JSON Export
        json_data = json.dumps({
            "application": "SEO National Local Transcriber Studio",
            "creator": "Rego",
            "speakers": st.session_state["speaker_names"],
            "segments": st.session_state["transcript"]
        }, indent=4)
        
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name="transcript.json",
            mime="application/json"
        )

    with col3:
        # SRT Subtitle Export
        srt_lines = []
        for i, seg in enumerate(st.session_state["transcript"], 1):
            def format_srt(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds - int(seconds)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
            name = st.session_state["speaker_names"].get(seg["speaker"], seg["speaker"])
            srt_lines.append(f"{i}\n{format_srt(seg['start'])} --> {format_srt(seg['end'])}\n{name}: {seg['text']}\n")
        
        st.download_button(
            label="Download as SRT Subtitles",
            data="\n".join(srt_lines),
            file_name="subtitles.srt",
            mime="text/plain"
        )