#!/usr/bin/env python3
"""
Step 2: Generate Scene Videos
"""
import json
import os

def main():
    print("🎬 GENERATING SCENE VIDEOS...")
    
    # Load scene instructions
    scene_files = [f for f in os.listdir('../video_output/scenes/') if f.endswith('.json')]
    
    print("📋 SCENE GENERATION INSTRUCTIONS:")
    print("=" * 60)
    
    for scene_file in sorted(scene_files):
        with open(f'../video_output/scenes/{scene_file}', 'r') as f:
            scene = json.load(f)
        
        print(f"\n🎥 SCENE {scene['scene']}:")
        print(f"Duration: {scene['duration']}")
        print(f"Description: {scene['description']}")
        print(f"Video Prompt: {scene['video_prompt']}")
        print("-" * 40)
    
    print("\n🎯 INSTRUCTIONS:")
    print("1. Use Stable Video Diffusion or AnimateDiff")
    print("2. Input character images + scene prompts")
    print("3. Generate 5-10 second clips per scene")
    print("4. Save to 'scene_videos/' folder")

if __name__ == "__main__":
    main()
