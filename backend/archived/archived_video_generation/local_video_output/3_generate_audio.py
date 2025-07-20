#!/usr/bin/env python3
"""
Step 3: Generate Character Voices using Bark
"""
import json
from bark import SAMPLE_RATE, generate_audio, preload_models
import scipy.io.wavfile as wavfile

def main():
    print("🎤 GENERATING CHARACTER VOICES...")
    
    # Load voice setup
    with open('voice_synthesis_setup.json', 'r') as f:
        setup = json.load(f)
    
    # Preload Bark models
    print("Loading Bark models...")
    preload_models()
    
    dialogue = setup['dialogue_scripts']
    
    for character, lines in dialogue.items():
        print(f"\n🗣️ Generating voice for {character}...")
        
        # Choose voice preset based on character
        if "Phil" in character:
            voice_preset = "v2/en_speaker_6"  # Confident male voice
        else:
            voice_preset = "v2/en_speaker_3"  # Younger male voice
        
        for i, line_data in enumerate(lines):
            text = line_data['text']
            emotion = line_data['emotion']
            
            # Add emotion markers for Bark
            if emotion == "excited":
                text = f"[enthusiastic] {text}"
            elif emotion == "questioning":
                text = f"[confused] {text}"
            
            print(f"  Generating: '{text}'")
            
            # Generate audio
            audio_array = generate_audio(text, history_prompt=voice_preset)
            
            # Save audio file
            filename = f"audio/{character.replace(' ', '_')}_{i+1}.wav"
            wavfile.write(filename, SAMPLE_RATE, audio_array)
    
    print("\n✅ Audio generation complete!")

if __name__ == "__main__":
    main()
