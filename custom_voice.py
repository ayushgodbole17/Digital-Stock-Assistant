import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer
import os
import torch

# Load pre-trained Wav2Vec 2.0 model and tokenizer
tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

def transcribe_audio(audio_path):
    waveform, sample_rate = torchaudio.load(audio_path)
    if sample_rate != 16000:
        transform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = transform(waveform)
    input_values = tokenizer(waveform.squeeze().numpy(), return_tensors="pt").input_values
    logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = tokenizer.decode(predicted_ids[0])
    return transcription.lower()

# Transcribe all audio files in a directory
audio_dir = r"C:\Users\Ayush\Desktop\KUL\Thesis\dataset_for_mfa\rapper_songs\rapper1"
transcriptions = {}
for file_name in os.listdir(audio_dir):
    if file_name.endswith(".wav"):
        file_path = os.path.join(audio_dir, file_name)
        transcription = transcribe_audio(file_path)
        transcriptions[file_name] = transcription
        print(f"Transcribed {file_name}: {transcription}")

# Save transcriptions to a file
with open("transcriptions.txt", "w") as f:
    for file_name, transcription in transcriptions.items():
        f.write(f"{file_name}|{transcription}\n")
