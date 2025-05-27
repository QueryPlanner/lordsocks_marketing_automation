import json
import random
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
import pandas as pd

@dataclass
class SockProduct:
    """Represents a sock product with its details"""
    id: str
    name: str
    description: str
    colors: List[str]
    style: str  # casual, athletic, dress, fun, etc.
    target_audience: str
    image_paths: List[str]  # paths to product images
    keywords: List[str]

@dataclass
class ContentStyle:
    """Defines the style parameters for content generation"""
    ad_style: str  # storytelling, humor, clean_focus, aesthetic, lifestyle
    voice_style: str  # male_casual, female_energetic, professional, quirky
    mood: str  # upbeat, calm, exciting, sophisticated
    target_emotion: str  # desire, comfort, confidence, fun

@dataclass
class ReelSpec:
    """Specification for a single reel"""
    format_type: str  # video_focused, mixed_media
    duration: int  # seconds
    sock_product: SockProduct
    content_style: ContentStyle
    video_prompts: List[str]
    image_prompts: List[str]
    voiceover_script: str

class SocksReelsPipeline:
    def __init__(self, gemini_api_key: str, output_dir: str = "generated_reels"):
        """Initialize the AI-powered reels creation pipeline"""
        self.gemini_api_key = gemini_api_key
        self.output_dir = output_dir
        self.setup_gemini()
        self.create_directories()
        
        # Load sock products and content styles
        self.sock_products = self.load_sock_products()
        self.content_styles = self.load_content_styles()
        
        # Performance tracking
        self.performance_log = []
    
    def setup_gemini(self):
        """Initialize Gemini AI client"""
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        print("✅ Gemini AI client initialized")
    
    def create_directories(self):
        """Create necessary directories for output"""
        dirs = [
            self.output_dir,
            f"{self.output_dir}/videos",
            f"{self.output_dir}/images", 
            f"{self.output_dir}/audio",
            f"{self.output_dir}/final_reels",
            "data"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_sock_products(self) -> List[SockProduct]:
        """Load sock products from JSON file or create sample data"""
        try:
            with open('data/sock_products.json', 'r') as f:
                data = json.load(f)
                # Handle both list format and object with 'products' key
                if isinstance(data, list):
                    products_data = data
                else:
                    products_data = data.get('products', [])
                return [SockProduct(**product) for product in products_data]
        except FileNotFoundError:
            # Create sample sock products
            sample_products = [
                SockProduct(
                    id="crew_001",
                    name="Urban Comfort Crew",
                    description="Premium cotton crew socks with moisture-wicking technology, perfect for all-day comfort in casual or office settings.",
                    colors=["black", "navy", "gray"],
                    style="casual",
                    target_audience="professionals_casual",
                    image_paths=["assets/crew_001_white_bg.jpg", "assets/crew_001_model.jpg"],
                    keywords=["comfort", "breathable", "professional", "versatile"]
                ),
                SockProduct(
                    id="athletic_002", 
                    name="Performance Runner",
                    description="High-performance athletic socks with cushioned heel and toe, designed for runners and active lifestyles.",
                    colors=["white", "black", "neon_green"],
                    style="athletic",
                    target_audience="fitness_enthusiasts",
                    image_paths=["assets/athletic_002_white_bg.jpg", "assets/athletic_002_model.jpg"],
                    keywords=["performance", "cushioned", "athletic", "moisture-wicking"]
                )
            ]
            # Save sample data
            with open('data/sock_products.json', 'w') as f:
                json.dump([asdict(product) for product in sample_products], f, indent=2)
            return sample_products
    
    def load_content_styles(self) -> List[ContentStyle]:
        """Load content style templates"""
        return [
            ContentStyle("storytelling", "female_energetic", "upbeat", "confidence"),
            ContentStyle("clean_focus", "male_professional", "calm", "trust"),
            ContentStyle("lifestyle", "female_casual", "exciting", "desire"),
            ContentStyle("humor", "male_quirky", "fun", "entertainment"),
            ContentStyle("aesthetic", "female_sophisticated", "sophisticated", "aspiration")
        ]
    
    def select_daily_socks(self, count: int = 5) -> List[SockProduct]:
        """Select socks for daily content creation"""
        if len(self.sock_products) >= count:
            return random.sample(self.sock_products, count)
        else:
            # If we have fewer products, repeat some
            selected = self.sock_products.copy()
            while len(selected) < count:
                selected.extend(random.sample(self.sock_products, 
                               min(count - len(selected), len(self.sock_products))))
            return selected[:count]
    
    def generate_reel_spec(self, sock: SockProduct) -> ReelSpec:
        """Generate a complete reel specification for a sock product"""
        # Randomly select format and style
        format_type = random.choice(["video_focused", "mixed_media"])
        content_style = random.choice(self.content_styles)
        duration = 16 if format_type == "video_focused" else random.randint(15, 20)
        
        # Generate prompts using Gemini
        video_prompts = self.generate_video_prompts(sock, content_style)
        image_prompts = self.generate_image_prompts(sock, content_style) if format_type == "mixed_media" else []
        voiceover_script = self.generate_voiceover_script(sock, content_style, duration)
        
        return ReelSpec(
            format_type=format_type,
            duration=duration,
            sock_product=sock,
            content_style=content_style,
            video_prompts=video_prompts,
            image_prompts=image_prompts,
            voiceover_script=voiceover_script
        )
    
    def generate_video_prompts(self, sock: SockProduct, style: ContentStyle) -> List[str]:
        """Generate 2 interconnected video prompts for Veo2"""
        prompt = f"""
        Create 2 interconnected 8-second video scene prompts for showcasing {sock.name} socks.
        
        Product: {sock.description}
        Style: {sock.style}
        Colors: {', '.join(sock.colors)}
        Ad Style: {style.ad_style}
        Mood: {style.mood}
        Target Emotion: {style.target_emotion}
        
        Requirements:
        - Each scene should be exactly 8 seconds
        - Scenes should flow together narratively
        - Focus on the socks and their benefits
        - Match the {style.ad_style} advertising style
        - Evoke {style.target_emotion}
        
        Return as JSON with keys "scene1" and "scene2", each containing a detailed prompt.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            # Clean the response text to remove markdown fences
            if response_text.startswith("```json"):
                response_text = response_text[response_text.find('{'):response_text.rfind('}')+1]
            
            result = json.loads(response_text)
            return [result["scene1"], result["scene2"]]
        except Exception as e:
            print(f"ERROR in generate_video_prompts: {e}")
            # Fallback prompts
            return [
                f"Close-up shot of feet wearing {sock.name} socks, walking confidently on various surfaces, emphasizing comfort and style",
                f"Lifestyle shot showing person in {sock.name} socks enjoying daily activities, highlighting the versatility and quality"
            ]
    
    def generate_image_prompts(self, sock: SockProduct, style: ContentStyle) -> List[str]:
        """Generate 5 image prompts for mixed media reels"""
        prompt = f"""
        Create 5 fashion-focused image prompts for {sock.name} socks using Gemini FASH 2.0.
        
        Product: {sock.description}
        Colors: {', '.join(sock.colors)}
        Style: {sock.style} 
        Ad Style: {style.ad_style}
        Mood: {style.mood}
        
        Each image should be 1 second in the final reel. Create variety:
        - Product shots
        - Lifestyle context
        - Detail shots
        - Styling shots
        - Emotional/aspirational shots
        
        Return as JSON array with 5 detailed prompts optimized for fashion e-commerce.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result if isinstance(result, list) else list(result.values())
        except:
            # Fallback image prompts
            return [
                f"Professional product shot of {sock.name} on clean white background",
                f"Flat lay styling shot with {sock.name} and complementary fashion items",
                f"Close-up detail of {sock.name} fabric texture and construction",
                f"Lifestyle shot of {sock.name} in everyday wear context",
                f"Artistic composition highlighting the premium quality of {sock.name}"
            ]
    
    def generate_voiceover_script(self, sock: SockProduct, style: ContentStyle, duration: int) -> str:
        """Generate voiceover script matching the content style"""
        prompt = f"""
        Write a {duration}-second voiceover script for {sock.name} socks.
        
        Product: {sock.description}
        Voice Style: {style.voice_style}
        Mood: {style.mood}
        Ad Style: {style.ad_style}
        Target Emotion: {style.target_emotion}
        
        Requirements:
        - Exactly {duration} seconds when spoken naturally
        - Match {style.voice_style} tone
        - Emphasize key benefits: {', '.join(sock.keywords)}
        - Include subtle call-to-action
        - Sound natural and engaging
        
        Return just the script text, no formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"Experience the comfort of {sock.name}. Premium quality that moves with you, all day long. Step into something better."
    
    def create_daily_reels(self, date: str = None) -> List[Dict]:
        """Create 5 reels for a specific day"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"🎬 Creating 5 reels for {date}")
        
        # Select socks for today
        daily_socks = self.select_daily_socks(5)
        reel_specs = []
        
        for i, sock in enumerate(daily_socks, 1):
            print(f"📝 Generating reel {i}/5: {sock.name}")
            spec = self.generate_reel_spec(sock)
            reel_specs.append(spec)
            
            # Save spec for reference
            spec_data = {
                "date": date,
                "reel_number": i,
                "sock_id": sock.id,
                "format_type": spec.format_type,
                "duration": spec.duration,
                "content_style": asdict(spec.content_style),
                "video_prompts": spec.video_prompts,
                "image_prompts": spec.image_prompts,
                "voiceover_script": spec.voiceover_script
            }
            
            # Save to JSON for manual processing
            output_file = f"{self.output_dir}/reel_{date}_{i:02d}_spec.json"
            with open(output_file, 'w') as f:
                json.dump(spec_data, f, indent=2)
            
            print(f"✅ Reel {i} specification saved to {output_file}")
        
        # Generate summary report
        self.generate_daily_report(date, reel_specs)
        
        return [asdict(spec) for spec in reel_specs]
    
    def generate_daily_report(self, date: str, reel_specs: List[ReelSpec]):
        """Generate a daily content report"""
        report = {
            "date": date,
            "total_reels": len(reel_specs),
            "format_breakdown": {},
            "style_breakdown": {},
            "socks_featured": [],
            "next_steps": [
                "1. Use video prompts with Veo2 API (5-6 videos max per day)",
                "2. Generate images with Gemini FASH 2.0",
                "3. Create voiceovers with Gemini Audio",
                "4. Assemble videos using provided specs",
                "5. Upload manually to Instagram",
                "6. Track performance metrics"
            ]
        }
        
        for spec in reel_specs:
            # Format breakdown
            format_type = spec.format_type
            report["format_breakdown"][format_type] = report["format_breakdown"].get(format_type, 0) + 1
            
            # Style breakdown
            ad_style = spec.content_style.ad_style
            report["style_breakdown"][ad_style] = report["style_breakdown"].get(ad_style, 0) + 1
            
            # Socks featured
            report["socks_featured"].append({
                "name": spec.sock_product.name,
                "style": spec.sock_product.style,
                "ad_style": spec.content_style.ad_style
            })
        
        # Save report
        report_file = f"{self.output_dir}/daily_report_{date}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Daily report saved to {report_file}")
    
    def track_performance(self, reel_id: str, metrics: Dict):
        """Track performance metrics for a reel"""
        performance_entry = {
            "reel_id": reel_id,
            "timestamp": datetime.now().isoformat(),
            **metrics
        }
        self.performance_log.append(performance_entry)
        
        # Save to CSV for easy analysis
        df = pd.DataFrame(self.performance_log)
        df.to_csv(f"{self.output_dir}/performance_tracking.csv", index=False)
        print(f"📈 Performance tracked for {reel_id}")
    
    def analyze_performance(self) -> Dict:
        """Analyze performance trends"""
        if not self.performance_log:
            return {"message": "No performance data available yet"}
        
        df = pd.DataFrame(self.performance_log)
        
        analysis = {
            "total_reels": len(df),
            "average_reach": df.get('reach', pd.Series()).mean(),
            "average_saves": df.get('saves', pd.Series()).mean(),
            "average_shares": df.get('shares', pd.Series()).mean(),
            "top_performing_reels": df.nlargest(3, 'reach')[['reel_id', 'reach']].to_dict('records') if 'reach' in df.columns else [],
            "insights": "Use this data to optimize future content creation"
        }
        
        return analysis

# Usage Example
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = SocksReelsPipeline(
        gemini_api_key="",
        output_dir="generated_reels"
    )
    
    # Create today's reels
    today_reels = pipeline.create_daily_reels()
    
    print(f"\n🎉 Generated {len(today_reels)} reel specifications!")
    print("Next steps:")
    print("1. Review the generated JSON files")
    print("2. Use prompts with Veo2 and FASH 2.0 APIs") 
    print("3. Assemble final videos")
    print("4. Upload to Instagram")
    print("5. Track performance using pipeline.track_performance()")