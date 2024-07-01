from pyrogram import Client, filters
import numpy as np
from pydub import AudioSegment
import os
import tempfile

def bitcrush(audio, bit_depth=8, sample_rate_reduction=4):
    # Reduce bit depth
    max_val = 2**(bit_depth - 1) - 1
    min_val = -2**(bit_depth - 1)
    quantized = np.round(audio * max_val) / max_val
    quantized = np.clip(quantized, min_val / max_val, max_val / max_val)

    # Reduce sample rate
    original_length = len(quantized)
    reduced_length = original_length // sample_rate_reduction
    downsampled = quantized[::sample_rate_reduction]
    upsampled = np.repeat(downsampled, sample_rate_reduction)[:original_length]

    return upsampled

def add_on_commands(app: Client):
    @app.on_message(filters.command("bitcrush", prefixes=".") & filters.reply)
    def bitcrush_command(client, message):
        if not message.reply_to_message or not message.reply_to_message.audio:
            message.reply_text("Please reply to an audio file (wav, mp3, ogg).")
            return

        # Download the audio file
        audio_file = client.download_media(message.reply_to_message.audio)
        audio = AudioSegment.from_file(audio_file)
        audio = audio.set_channels(1)  # Ensure audio is mono for simplicity

        # Convert audio to numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples /= np.iinfo(audio.array_type).max  # Normalize to [-1, 1]

        # Apply bitcrush effect with default bit depth 8 and sample rate reduction 4
        bitcrushed_samples = bitcrush(samples)

        # Convert back to audio segment
        bitcrushed_samples = (bitcrushed_samples * np.iinfo(audio.array_type).max).astype(audio.array_type)
        bitcrushed_audio = audio._spawn(bitcrushed_samples.tobytes())

        # Export bitcrushed audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            bitcrushed_audio.export(tmp_file.name, format="mp3")
            tmp_file_path = tmp_file.name
        
        # Send the bitcrushed audio file
        message.reply_audio(tmp_file_path, caption=f"Bitcrushed to 8b with sample rate reduction 4")

        # Clean up
        os.remove(audio_file)
        os.remove(tmp_file_path)