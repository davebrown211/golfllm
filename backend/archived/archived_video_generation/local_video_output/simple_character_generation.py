#!/usr/bin/env python3
"""
Simple Character Image Generation
Using web-based tools or simple local setup
"""
import json
import os

def display_character_prompts():
    """Display character prompts for easy copy-paste"""
    
    # Load our character data
    with open('stable_diffusion_setup.json', 'r') as f:
        setup = json.load(f)
    
    prompts = setup['character_prompts']
    
    print("🎨 CHARACTER IMAGE GENERATION")
    print("=" * 60)
    print("Choose your approach:\n")
    
    print("🌐 OPTION 1: WEB-BASED (EASIEST)")
    print("   • Leonardo.ai (15 free images/day)")
    print("   • Playground AI (100 free images/day)")  
    print("   • Bing Image Creator (free with Microsoft account)")
    print("   • Copy-paste prompts below")
    
    print("\n💻 OPTION 2: LOCAL STABLE DIFFUSION")
    print("   • Continue WebUI setup (takes time)")
    print("   • Full control, unlimited generations")
    
    print("\n📱 OPTION 3: PHONE APPS")
    print("   • Wombo Dream, Starryai, etc.")
    print("   • Quick and easy")
    
    print("\n" + "=" * 60)
    print("CHARACTER PROMPTS FOR COPY-PASTE:")
    print("=" * 60)
    
    for char_name, prompt_data in prompts.items():
        print(f"\n👤 {char_name.upper()}")
        print("-" * 40)
        print("PROMPT:")
        print(prompt_data['positive_prompt'])
        print("\nNEGATIVE PROMPT:")
        print(prompt_data['negative_prompt'])
        print("\nSTYLE:")
        print(prompt_data['style'])
        print("\n" + "="*40)
    
    print("\n🎯 INSTRUCTIONS:")
    print("1. Choose your preferred method above")
    print("2. Copy the character prompts")
    print("3. Generate 2-3 images per character")
    print("4. Save as: phil_mickelson_1.png, steve_1.png, etc.")
    print("5. Put in 'character_images/' folder")
    
    print("\n💡 TIP: Start with Leonardo.ai - it's free and works great!")
    print("   • Sign up at leonardo.ai")
    print("   • Select 'DreamShaper' model")
    print("   • Use 'Cinematic' style preset")

def create_web_generation_guide():
    """Create detailed guide for web-based generation"""
    
    guide = {
        "title": "Web-based Character Generation Guide",
        "recommended_platforms": {
            "leonardo_ai": {
                "url": "https://leonardo.ai",
                "free_tier": "15 generations per day",
                "model": "DreamShaper v7",
                "style": "Cinematic or Anime",
                "steps": [
                    "1. Sign up for free account",
                    "2. Click 'AI Image Generation'", 
                    "3. Select 'DreamShaper v7' model",
                    "4. Paste positive prompt",
                    "5. Add negative prompt",
                    "6. Set dimensions to 768x512 (landscape)",
                    "7. Generate 4 images",
                    "8. Download best ones"
                ]
            },
            "playground_ai": {
                "url": "https://playgroundai.com", 
                "free_tier": "100 generations per day",
                "model": "Stable Diffusion XL",
                "features": "Higher quality, more realistic"
            },
            "bing_creator": {
                "url": "https://www.bing.com/images/create",
                "free_tier": "Unlimited with Microsoft account",
                "model": "DALL-E 3",
                "features": "Very high quality, excellent at following prompts"
            }
        },
        "character_specifications": {
            "phil_mickelson": {
                "key_features": "Distinctive glasses, graying hair, confident pose",
                "clothing": "Golf apparel with branding",
                "setting": "Professional golf course"
            },
            "steve": {
                "key_features": "Yellow polo shirt, casual style", 
                "clothing": "Play Yellow polo, casual golf attire",
                "setting": "Golf course, relaxed atmosphere"
            }
        },
        "tips": [
            "Generate multiple variations of each character",
            "Save high-resolution versions",
            "Keep consistent lighting/style across characters",
            "Test different poses: standing, mid-swing, celebrating"
        ]
    }
    
    with open('web_generation_guide.json', 'w') as f:
        json.dump(guide, f, indent=2)
    
    print("📝 Detailed web generation guide saved to 'web_generation_guide.json'")

def check_character_images():
    """Check if character images have been generated"""
    
    image_dir = "character_images"
    if not os.path.exists(image_dir):
        print(f"❌ Directory '{image_dir}' not found")
        return False
    
    image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"❌ No images found in '{image_dir}'")
        return False
    
    print(f"✅ Found {len(image_files)} character images:")
    for img in sorted(image_files):
        print(f"   • {img}")
    
    return True

def main():
    """Main function"""
    print("🚀 SIMPLE CHARACTER GENERATION")
    print("Perfect for laptop/quick generation!\n")
    
    display_character_prompts()
    create_web_generation_guide()
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("📋 Next steps:")
    print("1. Visit one of the web platforms above")
    print("2. Generate character images using the prompts")
    print("3. Save them to character_images/ folder") 
    print("4. Run this script again to verify")
    
    print("\n🔍 Want to check your progress? Run:")
    print("   python simple_character_generation.py --check")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_character_images()
    else:
        main()