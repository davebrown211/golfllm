#!/usr/bin/env python3
"""
Step 1: Generate Character Images using Stable Diffusion
"""
import json
import os

def main():
    print("🎨 GENERATING CHARACTER IMAGES...")
    
    # Load character prompts
    with open('stable_diffusion_setup.json', 'r') as f:
        setup = json.load(f)
    
    prompts = setup['character_prompts']
    
    print("📋 CHARACTER PROMPTS TO USE IN STABLE DIFFUSION:")
    print("=" * 60)
    
    for char_name, prompt_data in prompts.items():
        print(f"\n👤 {char_name.upper()}:")
        print(f"Positive: {prompt_data['positive_prompt']}")
        print(f"Negative: {prompt_data['negative_prompt']}")
        print(f"Style: {prompt_data['style']}")
        print("-" * 40)
    
    print("\n🎯 INSTRUCTIONS:")
    print("1. Start Automatic1111 WebUI (http://127.0.0.1:7860)")
    print("2. Use above prompts to generate 2-3 images per character")
    print("3. Save images to 'character_images/' folder")
    print("4. Name files: 'phil_mickelson_1.png', 'grant_horvat_1.png', etc.")

if __name__ == "__main__":
    main()
