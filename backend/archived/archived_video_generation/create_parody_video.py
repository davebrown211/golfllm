#!/usr/bin/env python3
"""
Generate a parody video script using character data
"""
import sys
sys.path.append('youtube_analyzer')
import json

from youtube_analyzer.app.video_script_generator import generate_video_script

def create_video():
    """Generate and display a parody video script"""
    print("=== GOLF PARODY VIDEO GENERATOR ===")
    print("Using character data from database...\n")
    
    # Generate challenge video script
    script = generate_video_script(video_type="challenge", duration=3)
    
    if "error" in script:
        print(f"❌ Error: {script['error']}")
        print("Make sure you have character data in the database first!")
        return
    
    # Display the generated script
    print(f"🎬 TITLE: {script['title']}")
    print(f"⏱️  DURATION: {script['total_duration']}")
    print(f"💡 CONCEPT: {script['concept']}")
    print("\n" + "="*60)
    
    # Display each scene
    for scene in script['scenes']:
        print(f"\n🎥 SCENE {scene['scene_number']} ({scene['duration']})")
        print(f"📍 LOCATION: {scene['location']}")
        print(f"📝 DESCRIPTION: {scene['description']}")
        print("\n💬 DIALOGUE:")
        
        for line in scene['dialogue']:
            character = line['character']
            dialogue = line['line']
            action = line.get('action', '')
            
            print(f"\n{character}:")
            print(f"  \"{dialogue}\"")
            if action:
                print(f"  [{action}]")
    
    # Display character notes
    print(f"\n{'='*60}")
    print("🎭 CHARACTER PRODUCTION NOTES:")
    
    for char_name, notes in script['character_notes'].items():
        print(f"\n👤 {char_name.upper()}:")
        
        costume = notes['costume']
        print(f"  👔 COSTUME:")
        print(f"    - Clothing: {costume['clothing']}")
        print(f"    - Accessories: {costume['accessories']}")
        print(f"    - Features: {costume['distinctive_features']}")
        
        personality = notes['personality']
        print(f"  🧠 PERSONALITY:")
        print(f"    - Confidence: {personality['confidence']}/10")
        print(f"    - Humor: {personality['humor']}/10")
        
        print(f"  🎬 ACTING NOTES:")
        for note in notes['acting_notes']:
            print(f"    - {note}")
    
    # Display production notes
    print(f"\n{'='*60}")
    print("📹 PRODUCTION NOTES:")
    for note in script['production_notes']:
        print(f"  • {note}")
    
    print(f"\n{'='*60}")
    print("✅ Video script generated successfully!")
    print("\nNext steps:")
    print("1. 🎯 Choose video generation platform (Runway Gen-3, Stable Video)")
    print("2. 📸 Create character reference images")
    print("3. 🎬 Generate video scenes using AI")
    print("4. ✂️  Edit together with dialogue/music")

def save_script_to_file():
    """Generate script and save to JSON file"""
    script = generate_video_script(video_type="challenge", duration=3)
    
    if "error" not in script:
        with open('generated_video_script.json', 'w') as f:
            json.dump(script, f, indent=2)
        print("💾 Script saved to 'generated_video_script.json'")
    
    return script

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        save_script_to_file()
    else:
        create_video()