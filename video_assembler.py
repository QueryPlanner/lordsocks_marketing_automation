import json
import os
from moviepy.editor import *
from typing import List, Dict
import requests
from datetime import datetime

class ReelAssembler:
    """Assembles videos, images, and audio into final Instagram reels"""
    
    def __init__(self, assets_dir: str = "generated_reels"):
        self.assets_dir = assets_dir
        self.video_dir = f"{assets_dir}/videos"
        self.image_dir = f"{assets_dir}/images"
        self.audio_dir = f"{assets_dir}/audio"
        self.output_dir = f"{assets_dir}/final_reels"
    
    def load_reel_spec(self, spec_file: str) -> Dict:
        """Load reel specification from JSON file"""
        with open(spec_file, 'r') as f:
            return json.load(f)
    
    def assemble_video_focused_reel(self, spec: Dict, video_files: List[str], audio_file: str) -> str:
        """Assemble a video-focused reel (2 videos + audio)"""
        print(f"🎬 Assembling video-focused reel...")
        
        # Load video clips
        clips = []
        for video_file in video_files[:2]:  # Use first 2 videos
            if os.path.exists(video_file):
                clip = VideoFileClip(video_file).resize(height=1920).crop(x_center=clip.w/2, width=1080)
                clips.append(clip)
        
        if not clips:
            raise ValueError("No video files found")
        
        # Concatenate videos
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add audio if provided
        if audio_file and os.path.exists(audio_file):
            audio = AudioFileClip(audio_file)
            final_video = final_video.set_audio(audio)
        
        # Export
        output_path = f"{self.output_dir}/reel_{spec['date']}_{spec['reel_number']:02d}.mp4"
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        if 'audio' in locals():
            audio.close()
        
        print(f"✅ Video-focused reel saved: {output_path}")
        return output_path
    
    def assemble_mixed_media_reel(self, spec: Dict, video_files: List[str], image_files: List[str], audio_file: str) -> str:
        """Assemble a mixed media reel (2 videos + 4-5 images + audio)"""
        print(f"🎨 Assembling mixed media reel...")
        
        clips = []
        
        # Add first video (8 seconds)
        if len(video_files) > 0 and os.path.exists(video_files[0]):
            video1 = VideoFileClip(video_files[0]).resize(height=1920).crop(x_center=video1.w/2, width=1080)
            clips.append(video1)
        
        # Add images (1 second each)
        for image_file in image_files[:5]:
            if os.path.exists(image_file):
                img_clip = ImageClip(image_file, duration=1).resize(height=1920).crop(x_center=img_clip.w/2, width=1080)
                clips.append(img_clip)
        
        # Add second video (8 seconds)
        if len(video_files) > 1 and os.path.exists(video_files[1]):
            video2 = VideoFileClip(video_files[1]).resize(height=1920).crop(x_center=video2.w/2, width=1080)
            clips.append(video2)
        
        if not clips:
            raise ValueError("No media files found")
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add audio
        if audio_file and os.path.exists(audio_file):
            audio = AudioFileClip(audio_file)
            final_video = final_video.set_audio(audio)
        
        # Export
        output_path = f"{self.output_dir}/reel_{spec['date']}_{spec['reel_number']:02d}.mp4"
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        if 'audio' in locals():
            audio.close()
        
        print(f"✅ Mixed media reel saved: {output_path}")
        return output_path
    
    def assemble_reel_from_spec(self, spec_file: str) -> str:
        """Assemble a reel based on its specification file"""
        spec = self.load_reel_spec(spec_file)
        
        # Expected file paths based on spec
        date = spec['date']
        reel_num = spec['reel_number']
        
        video_files = [
            f"{self.video_dir}/reel_{date}_{reel_num:02d}_video1.mp4",
            f"{self.video_dir}/reel_{date}_{reel_num:02d}_video2.mp4"
        ]
        
        image_files = [
            f"{self.image_dir}/reel_{date}_{reel_num:02d}_img{i}.jpg" 
            for i in range(1, 6)
        ]
        
        audio_file = f"{self.audio_dir}/reel_{date}_{reel_num:02d}_voiceover.mp3"
        
        # Assemble based on format type
        if spec['format_type'] == 'video_focused':
            return self.assemble_video_focused_reel(spec, video_files, audio_file)
        else:
            return self.assemble_mixed_media_reel(spec, video_files, image_files, audio_file)

class PerformanceTracker:
    """Track Instagram reel performance metrics"""
    
    def __init__(self, tracking_file: str = "performance_data.json"):
        self.tracking_file = tracking_file
        self.load_data()
    
    def load_data(self):
        """Load existing performance data"""
        try:
            with open(self.tracking_file, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = []
    
    def save_data(self):
        """Save performance data to file"""
        with open(self.tracking_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_reel_performance(self, reel_info: Dict):
        """Add performance data for a reel"""
        entry = {
            "reel_id": reel_info.get("reel_id"),
            "date_posted": reel_info.get("date_posted"),
            "sock_product": reel_info.get("sock_product"),
            "format_type": reel_info.get("format_type"),
            "content_style": reel_info.get("content_style"),
            "metrics": reel_info.get("metrics", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        self.data.append(entry)
        self.save_data()
        print(f"📊 Performance data added for {entry['reel_id']}")
    
    def get_performance_summary(self) -> Dict:
        """Get summary of performance metrics"""
        if not self.data:
            return {"message": "No performance data available"}
        
        total_reels = len(self.data)
        
        # Calculate averages
        metrics = ['reach', 'saves', 'shares', 'comments', 'profile_visits']
        averages = {}
        
        for metric in metrics:
            values = [entry['metrics'].get(metric, 0) for entry in self.data if entry['metrics'].get(metric)]
            averages[f"avg_{metric}"] = sum(values) / len(values) if values else 0
        
        # Find best performing content
        best_reach = max(self.data, key=lambda x: x['metrics'].get('reach', 0))
        best_saves = max(self.data, key=lambda x: x['metrics'].get('saves', 0))
        
        return {
            "total_reels": total_reels,
            "averages": averages,
            "best_reach": {
                "reel_id": best_reach['reel_id'],
                "reach": best_reach['metrics'].get('reach', 0),
                "content_style": best_reach.get('content_style', {}).get('ad_style')
            },
            "best_saves": {
                "reel_id": best_saves['reel_id'], 
                "saves": best_saves['metrics'].get('saves', 0),
                "content_style": best_saves.get('content_style', {}).get('ad_style')
            }
        }
    
    def export_to_csv(self, filename: str = "performance_export.csv"):
        """Export performance data to CSV for analysis"""
        import pandas as pd
        
        # Flatten the data
        flattened_data = []
        for entry in self.data:
            flat_entry = {
                "reel_id": entry["reel_id"],
                "date_posted": entry["date_posted"],
                "sock_product": entry["sock_product"],
                "format_type": entry["format_type"],
                "ad_style": entry.get("content_style", {}).get("ad_style"),
                "voice_style": entry.get("content_style", {}).get("voice_style"),
                "mood": entry.get("content_style", {}).get("mood"),
                **entry["metrics"]
            }
            flattened_data.append(flat_entry)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False)
        print(f"📈 Performance data exported to {filename}")

class ContentCalendar:
    """Manage content planning and optimization"""
    
    def __init__(self):
        self.calendar_file = "content_calendar.json"
        self.load_calendar()
    
    def load_calendar(self):
        """Load existing calendar data"""
        try:
            with open(self.calendar_file, 'r') as f:
                self.calendar = json.load(f)
        except FileNotFoundError:
            self.calendar = {}
    
    def save_calendar(self):
        """Save calendar data"""
        with open(self.calendar_file, 'w') as f:
            json.dump(self.calendar, f, indent=2)
    
    def plan_week(self, start_date: str, sock_priorities: List[str] = None):
        """Plan content for a week based on performance insights"""
        from datetime import datetime, timedelta
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        week_plan = {}
        
        for i in range(7):
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            week_plan[date] = {
                "planned_socks": sock_priorities[:5] if sock_priorities else [],
                "content_focus": self.get_daily_focus(i),
                "posting_time": "10:00 AM",  # Customize based on audience insights
                "hashtag_strategy": self.get_hashtag_strategy(i)
            }
        
        self.calendar[f"week_{start_date}"] = week_plan
        self.save_calendar()
        
        return week_plan
    
    def get_daily_focus(self, day_of_week: int) -> str:
        """Get content focus based on day of week"""
        focuses = [
            "motivation_monday",      # 0 - Monday
            "tips_tuesday",          # 1 - Tuesday  
            "workout_wednesday",     # 2 - Wednesday
            "throwback_thursday",    # 3 - Thursday
            "fashion_friday",        # 4 - Friday
            "style_saturday",        # 5 - Saturday
            "comfort_sunday"         # 6 - Sunday
        ]
        return focuses[day_of_week]
    
    def get_hashtag_strategy(self, day_of_week: int) -> List[str]:
        """Get hashtag strategy for the day"""
        base_tags = ["#socks", "#comfort", "#style", "#fashion"]
        
        day_specific = {
            0: ["#MotivationMonday", "#NewWeek"],
            1: ["#TipsTuesday", "#LifeHacks"], 
            2: ["#WorkoutWednesday", "#Fitness"],
            3: ["#ThrowbackThursday", "#Memories"],
            4: ["#FashionFriday", "#OOTD"],
            5: ["#StyleSaturday", "#Weekend"],
            6: ["#ComfortSunday", "#Relax"]
        }
        
        return base_tags + day_specific.get(day_of_week, [])

# Usage example
if __name__ == "__main__":
    # Initialize components
    assembler = ReelAssembler()
    tracker = PerformanceTracker()
    calendar = ContentCalendar()
    
    print("🚀 Socks Reels Pipeline Tools Ready!")
    print("\nAvailable functions:")
    print("1. assembler.assemble_reel_from_spec('spec_file.json')")
    print("2. tracker.add_reel_performance(reel_data)")
    print("3. tracker.get_performance_summary()")
    print("4. calendar.plan_week('2025-05-26')")
    
    # Example workflow
    print("\n📋 Example Daily Workflow:")
    print("1. Run main pipeline to generate reel specs")
    print("2. Use Veo2 API with video prompts")
    print("3. Use FASH 2.0 API with image prompts") 
    print("4. Generate voiceovers with Gemini Audio")
    print("5. Use assembler to create final videos")
    print("6. Upload manually to Instagram")
    print("7. Track performance with tracker")