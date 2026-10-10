"""
Deterministic Seed Data Generator for FRAME.
Conforms to Section 22 of the Master Specification:
- 12 diverse realistic creators across AI film, 3D architecture, virtual avatars, product viz, anime, and NeRF
- Sample brands (public and confidential)
- Sample briefs, projects, milestones, conversations, messages, transactions, achievements, and trust events
- All explicitly marked as demo data
"""

import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from server.db.models import (
    Profile, CreatorProfile, BrandProfile, PortfolioItem, FeedPost,
    CreativeBrief, Project, ProjectMilestone, Conversation,
    ConversationParticipant, Message, Transaction, PayoutRecord,
    Subscription, VerificationRecord, TrustEvent, UserAchievement
)
from server.services.auth_service import AuthService
from server.services.achievements import AchievementEngine

CREATOR_SEEDS = [
    {
        "id": "creator_05",
        "username": "mercer_films",
        "display_name": "Julian Mercer",
        "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
        "bio": "Award-winning generative filmmaker. Directs full cinematic AI commercials, music videos, and brand teasers with temporal consistency, camera motion control, and multi-track audio sync.",
        "specializations": ["AI Filmmaking", "Neural VFX", "Runway Gen-3 Directing"],
        "skills": ["Temporal Consistency", "Camera Motion Control", "Audio Sync", "Multi-Pass Video Upscaling", "Cinematic Lighting"],
        "industries": ["Footwear", "Automotive", "Entertainment", "Beverage"],
        "ai_tools": ["Runway Gen-3 Alpha", "ComfyUI", "Luma Ray 2", "Kling AI", "Topaz Video AI"],
        "ai_models": ["Gen-3 Alpha", "Ray 2", "Kling 1.5", "Flux.1 Dev"],
        "workflow_description": "Custom 3-stage temporal smoothing pipeline with depth-guided ControlNet and seed-locked camera vectors.",
        "experience_years": 4.5,
        "content_types": ["Social Video Commercial", "AI Short Film", "Music Video", "Product Teaser"],
        "supported_platforms": ["Instagram Reels", "TikTok", "YouTube 4K", "Cinema Display"],
        "aspect_ratios": ["9:16 (Vertical Reels/TikTok)", "16:9 (Cinema / YouTube 4K)", "1:1 (Square)"],
        "minimum_budget": 3000.0,
        "maximum_budget": 15000.0,
        "hourly_compute_rate": 65.0,
        "base_model": "Runway Gen-3 Alpha + Luma Ray 2",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Quantum Velocity • Sneaker Motion",
                "content_type": "Social Video Commercial",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-futuristic-city-with-flying-cars-and-tall-buildings-42548-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "9:16",
                "style_tags": ["Cyberpunk", "Kinetic Neon", "Liquid Splashes", "Slow Motion"],
                "evidence_status": "c2pa_signed"
            },
            {
                "title": "Glacier Horizon Autonomous EV",
                "content_type": "AI Short Film",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-car-driving-through-a-futuristic-tunnel-42544-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "16:9",
                "style_tags": ["Anamorphic", "Photorealism", "Nordic Glaciers", "Volumetric Aurora"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_01",
        "username": "elena_arch",
        "display_name": "Elena Rostova",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
        "bio": "Lead visual architect previously at Foster+Partners. Fine-tuned custom LoRA stacks for monolithic neo-tokyo structures with dynamic volumetrics.",
        "specializations": ["Cyber-Brutalist Architecture", "Sci-Fi Environments", "Concept Art"],
        "skills": ["LoRA Fine-Tuning", "Volumetric Fog Rendering", "ComfyUI Node DAG", "Architectural CAD Infusion"],
        "industries": ["Architecture", "Real Estate", "Gaming", "Film Pre-Viz"],
        "ai_tools": ["ComfyUI", "SDXL Base 1.0", "Custom LoRA v3", "Topaz Gigapixel AI", "ControlNet Depth"],
        "ai_models": ["SDXL Base 1.0", "Flux.1 Dev"],
        "workflow_description": "AST-audited node graphs for deterministic high-resolution brutalist spatial structures.",
        "experience_years": 5.0,
        "content_types": ["3D Architectural Render", "Concept Art", "Commercial Stills"],
        "supported_platforms": ["Digital Billboards", "Print Lookbooks", "Instagram"],
        "aspect_ratios": ["16:9 (Cinema)", "21:9 (Ultrawide)", "4:5 (Social)"],
        "minimum_budget": 2500.0,
        "maximum_budget": 12000.0,
        "hourly_compute_rate": 45.0,
        "base_model": "SDXL Base 1.0 + Custom Brutalist LoRA v3",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Neo-Megastructure Atrium 07",
                "content_type": "3D Architectural Render",
                "media_path": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
                "thumbnail_path": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "16:9",
                "style_tags": ["Brutalism", "Cyberpunk", "Monolithic", "Volumetric Fog"],
                "evidence_status": "ast_verified"
            }
        ]
    },
    {
        "id": "creator_06",
        "username": "maya_neural",
        "display_name": "Maya Lin",
        "avatar_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=200&q=80",
        "bio": "Creator of autonomous synthetic virtual ambassadors with zero-drift identity persistence and neural speech lip-sync.",
        "specializations": ["Virtual Influencer UGC", "Neural Avatar Consistency", "Lip-Sync"],
        "skills": ["Facial Motion Capture AI", "Multi-Angle Consistency", "Audio-Driven Lip Sync", "UGC Scripting"],
        "industries": ["Skincare", "Cosmetics", "Apparel", "Consumer Tech"],
        "ai_tools": ["FLUX.1 Dev", "Hedra AI", "ComfyUI FaceID", "ElevenLabs", "LivePortrait"],
        "ai_models": ["Flux.1 Dev", "Hedra Character-v2"],
        "workflow_description": "Dual-LoRA FaceID conditioning coupled with voice-driven micro-expression synthesis.",
        "experience_years": 3.0,
        "content_types": ["Virtual Influencer UGC", "Product Review Video", "Social Ad"],
        "supported_platforms": ["TikTok", "Instagram Reels", "YouTube Shorts"],
        "aspect_ratios": ["9:16 (Vertical Reels/TikTok)"],
        "minimum_budget": 2000.0,
        "maximum_budget": 8000.0,
        "hourly_compute_rate": 50.0,
        "base_model": "FLUX.1 Dev + Hedra AI + LivePortrait",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Aria • AI Skincare Routine Testimonial",
                "content_type": "Virtual Influencer UGC",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-young-woman-talking-on-video-call-42352-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "9:16",
                "style_tags": ["Photorealistic Avatar", "Natural Sunlight", "UGC Testimonial"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_02",
        "username": "vance_cinematics",
        "display_name": "Liam Vance",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
        "bio": "Cinematographer turned generative AI director. Specializes in dystopian cinematic worldbuilding, high-speed camera tracking, and neural grading.",
        "specializations": ["Cinematic Camera Tracking", "Dystopian Sci-Fi", "Music Videos"],
        "skills": ["Kling Camera Paths", "Multi-Pass Denoising", "DaVinci Color Matching", "Temporal Coherence"],
        "industries": ["Music", "Fashion", "Gaming Trailers"],
        "ai_tools": ["Kling AI", "Runway Gen-3", "DaVinci Resolve Studio", "Topaz Video AI"],
        "ai_models": ["Kling 1.5 Pro", "Gen-3 Alpha"],
        "workflow_description": "Interpolated frame guidance with color-space ACES pipeline.",
        "experience_years": 4.0,
        "content_types": ["AI Short Film", "Music Video", "Brand Teaser"],
        "supported_platforms": ["YouTube 4K", "Vimeo", "Cinema 4K"],
        "aspect_ratios": ["16:9 (Cinema)", "2.39:1 (Anamorphic)"],
        "minimum_budget": 3500.0,
        "maximum_budget": 16000.0,
        "hourly_compute_rate": 60.0,
        "base_model": "Kling AI + Runway Gen-3 Alpha",
        "availability_status": "busy",
        "portfolio": [
            {
                "title": "Neon Monoliths • Dystopian Drift",
                "content_type": "AI Short Film",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-virtual-reality-tunnel-with-purple-and-blue-lights-42540-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "16:9",
                "style_tags": ["Dystopian", "Anamorphic", "Rainy Streets"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_07",
        "username": "priya_reels",
        "display_name": "Priya Sharma",
        "avatar_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80",
        "bio": "High-velocity social media editor and AI colorist. Masters emotional event recaps, birthday reels, and wedding montages with Kodachrome grain.",
        "specializations": ["Event Montages", "Birthday Reels", "Color Grading"],
        "skills": ["Beat-Synced Editing", "Kodachrome Grading", "Sound Design", "Kinetic Subtitles"],
        "industries": ["Events", "Lifestyle", "Weddings", "Creator Brands"],
        "ai_tools": ["Premiere Pro", "CapCut Pro", "Topaz Video AI", "Midjourney v6"],
        "ai_models": ["Midjourney v6.1", "Topaz Iris LQ"],
        "workflow_description": "Speed-ramp beat sync matched to viral audio stems with Topaz facial restoration.",
        "experience_years": 3.5,
        "content_types": ["Birthday / Event Montage", "Social Video Reel", "Wedding Teaser"],
        "supported_platforms": ["Instagram Reels", "TikTok", "YouTube Shorts"],
        "aspect_ratios": ["9:16 (Vertical Reels/TikTok)"],
        "minimum_budget": 1500.0,
        "maximum_budget": 6000.0,
        "hourly_compute_rate": 30.0,
        "base_model": "Topaz Video AI + Midjourney v6",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Golden Hour Wedding Recap",
                "content_type": "Birthday / Event Montage",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-hands-holding-a-sparkler-at-night-42354-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "9:16",
                "style_tags": ["Warm Kodachrome", "Golden Hour", "Emotional Cut"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_04",
        "username": "thorne_product",
        "display_name": "Marcus Thorne",
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80",
        "bio": "Industrial designer and CGI director. Renders organic biomorphic product visualization, liquid glass refractions, and luxury packaging lookbooks.",
        "specializations": ["Product Visualization", "Biomorphic 3D", "Luxury Packaging"],
        "skills": ["Glass Refraction", "Studio Softbox Lighting", "Parametric LoRA", "Macro Raytracing"],
        "industries": ["Fragrance", "Luxury Goods", "Furniture", "Electronics"],
        "ai_tools": ["SDXL Base 1.0", "ComfyUI", "Parametric LoRA", "Magnific AI", "Octane"],
        "ai_models": ["SDXL 1.0", "Custom Biomorphic LoRA"],
        "workflow_description": "Parametric material injection with physically based caustic reflections.",
        "experience_years": 6.0,
        "content_types": ["Product Visualization", "Commercial Stills", "Packaging Key Art"],
        "supported_platforms": ["Instagram Feed", "Print Billboard", "E-Commerce"],
        "aspect_ratios": ["4:5 (Social)", "1:1 (Square)", "16:9 (Display)"],
        "minimum_budget": 3000.0,
        "maximum_budget": 14000.0,
        "hourly_compute_rate": 55.0,
        "base_model": "SDXL Base 1.0 + Magnific AI",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Aura Luxury Flacon No. 5",
                "content_type": "Product Visualization",
                "media_path": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=800&q=80",
                "thumbnail_path": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "4:5",
                "style_tags": ["Biomorphic Minimal", "Glass Caustics", "Neutral Studio"],
                "evidence_status": "ast_verified"
            }
        ]
    },
    {
        "id": "creator_03",
        "username": "chloe_vfx",
        "display_name": "Chloe Bennett",
        "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80",
        "bio": "Fashion VFX artist and digital couturier. Merges haute couture garment physics with fast-diffusion editorial reels for Vogue and Prada.",
        "specializations": ["Fashion Editorial", "Digital Couture", "Haute Couture Physics"],
        "skills": ["Fabric Dynamics AI", "Editorial Lighting", "Runway Flow", "Style Transfer"],
        "industries": ["High Fashion", "Jewelry", "Cosmetics"],
        "ai_tools": ["FLUX.1 Schnell", "ComfyUI", "Topaz Video AI", "EbSynth"],
        "ai_models": ["Flux.1 Schnell", "AnimateDiff Motion-v3"],
        "workflow_description": "Diffusion-guided dynamic fabric draping with high-speed keyframe optical flow.",
        "experience_years": 3.2,
        "content_types": ["Social Video Commercial", "Fashion Editorial", "Digital Runway"],
        "supported_platforms": ["Instagram Reels", "TikTok", "Digital OOH"],
        "aspect_ratios": ["9:16 (Vertical Reels/TikTok)", "4:5 (Social)"],
        "minimum_budget": 2800.0,
        "maximum_budget": 11000.0,
        "hourly_compute_rate": 48.0,
        "base_model": "FLUX.1 Schnell + AnimateDiff",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Liquid Silk Mirage 2026",
                "content_type": "Social Video Commercial",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-model-posing-in-a-futuristic-studio-42546-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "9:16",
                "style_tags": ["Haute Couture", "Liquid Silk", "Avant-Garde"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_08",
        "username": "aarav_motion",
        "display_name": "Aarav Patel",
        "avatar_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=200&q=80",
        "bio": "Viral rhythm editor and motion designer. Builds high-conversion social drops, dynamic soundscapes, and beat-locked kinetic reels.",
        "specializations": ["Kinetic Typography", "Viral Beat Sync", "Brand Reels"],
        "skills": ["Kinetic Captions", "Sound Design", "Speed Ramping", "Audio Reactivity"],
        "industries": ["Streetwear", "Fitness", "Beverage", "Podcasts"],
        "ai_tools": ["CapCut Pro", "Premiere Pro", "After Effects", "ElevenLabs"],
        "ai_models": ["ElevenLabs Multilingual v2"],
        "workflow_description": "Audio stem transient detection tied to keyframe speed curve automation.",
        "experience_years": 2.8,
        "content_types": ["Social Video Reel", "Product Teaser", "Promo Drop"],
        "supported_platforms": ["TikTok", "Instagram Reels", "YouTube Shorts"],
        "aspect_ratios": ["9:16 (Vertical Reels/TikTok)"],
        "minimum_budget": 1200.0,
        "maximum_budget": 5000.0,
        "hourly_compute_rate": 25.0,
        "base_model": "After Effects + Topaz Video AI",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Energy Drop • 15s Kinetic Rhythm",
                "content_type": "Social Video Reel",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-young-man-dancing-in-a-neon-room-42542-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "9:16",
                "style_tags": ["Kinetic Rhythm", "Neon Energy", "Fast Cuts"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_09",
        "username": "kenji_anime",
        "display_name": "Kenji Sato",
        "avatar_url": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=200&q=80",
        "bio": "Tokyo-based anime director. Produces authentic neo-shonen and cyberpunk anime sequences with custom line-art ControlNet and hand-drawn cel shading.",
        "specializations": ["Anime Production", "Cel-Shading AI", "Sakuga Action"],
        "skills": ["LineArt ControlNet", "Sakuga Animation", "Color Scripting", "Character Sheets"],
        "industries": ["Gaming", "Anime", "Streaming", "Apparel"],
        "ai_tools": ["ComfyUI", "AnimateDiff", "ControlNet LineArt", "EbSynth"],
        "ai_models": ["Custom CelShader-SDXL", "AnimateDiff v3"],
        "workflow_description": "LineArt raster conditioning with multi-layer cel composite passes.",
        "experience_years": 4.1,
        "content_types": ["AI Short Film", "Social Video Reel", "Gaming Teaser"],
        "supported_platforms": ["YouTube", "Twitter/X", "Instagram Reels"],
        "aspect_ratios": ["16:9 (Cinema)", "9:16 (Vertical)"],
        "minimum_budget": 3200.0,
        "maximum_budget": 13000.0,
        "hourly_compute_rate": 50.0,
        "base_model": "ComfyUI + AnimateDiff + LineArt",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Tokyo Phantom 2099 Action Cut",
                "content_type": "AI Short Film",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-cyberpunk-soldier-aiming-with-a-rifle-42547-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "16:9",
                "style_tags": ["Neo-Tokyo", "Cel-Shaded Anime", "Sakuga"],
                "evidence_status": "ast_verified"
            }
        ]
    },
    {
        "id": "creator_10",
        "username": "sarah_doc",
        "display_name": "Sarah Jenkins",
        "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80",
        "bio": "Documentary filmmaker specializing in historical preservation, archival AI upscaling, and photo-real narrative reenactments.",
        "specializations": ["Archival Restoration", "Documentary Reenactment", "Deep Temporal Restoration"],
        "skills": ["Historical Accuracy AI", "Film Grain Emulation", "Voice Clone Narrative", "Super-Resolution"],
        "industries": ["Broadcasting", "Museums", "Documentaries", "Education"],
        "ai_tools": ["Topaz Video AI", "FLUX.1 Dev", "ElevenLabs", "DaVinci Resolve"],
        "ai_models": ["Flux.1 Dev", "Topaz Chronos"],
        "workflow_description": "Dual-frame optical interpolation with historical accuracy photo match.",
        "experience_years": 6.5,
        "content_types": ["AI Short Film", "Documentary Segment", "Historical Reenactment"],
        "supported_platforms": ["YouTube 4K", "Broadcast Television", "Museum Kiosk"],
        "aspect_ratios": ["16:9 (Cinema)", "4:3 (Archival)"],
        "minimum_budget": 4000.0,
        "maximum_budget": 18000.0,
        "hourly_compute_rate": 55.0,
        "base_model": "FLUX.1 Dev + Topaz Chronos",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Echoes of Apollo: Restored Lunar Feat",
                "content_type": "AI Short Film",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-space-view-of-planet-earth-42541-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "16:9",
                "style_tags": ["Archival 35mm", "Restored Footage", "Documentary"],
                "evidence_status": "c2pa_signed"
            }
        ]
    },
    {
        "id": "creator_11",
        "username": "dev_3d",
        "display_name": "Devansh Kapoor",
        "avatar_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=200&q=80",
        "bio": "Spatial computing and 3D Gaussian Splatting specialist. Converts live-action scene photogrammetry into navigable volumetric digital twins.",
        "specializations": ["3D Gaussian Splatting", "NeRF Environments", "Spatial Video"],
        "skills": ["Gaussian Splat Optimization", "Camera Trajectory Extraction", "Unreal Engine 5 Ingestion"],
        "industries": ["Spatial Computing", "Metaverse", "Luxury Real Estate", "VFX"],
        "ai_tools": ["Luma AI", "Postshot", "ComfyUI", "Unreal Engine 5.4"],
        "ai_models": ["3DGS-v2", "Depth-Anything-v2"],
        "workflow_description": "Point cloud extraction downsampled to 60fps real-time camera dolly sweeps.",
        "experience_years": 3.8,
        "content_types": ["Spatial Video", "3D Architectural Render", "Interactive Scene"],
        "supported_platforms": ["Apple Vision Pro", "WebXR", "YouTube 360"],
        "aspect_ratios": ["16:9 (Cinema)", "1:1 (Spatial)"],
        "minimum_budget": 4500.0,
        "maximum_budget": 20000.0,
        "hourly_compute_rate": 70.0,
        "base_model": "Postshot + Luma AI + UE5",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Volumetric Villa: 3D Gaussian Splat",
                "content_type": "3D Architectural Render",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-modern-living-room-with-a-view-of-the-city-42543-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "16:9",
                "style_tags": ["Gaussian Splat", "Volumetric", "Spatial 4K"],
                "evidence_status": "ast_verified"
            }
        ]
    },
    {
        "id": "creator_12",
        "username": "fatima_visuals",
        "display_name": "Fatima Zahra",
        "avatar_url": "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?auto=format&fit=crop&w=200&q=80",
        "bio": "Art director and botanical 3D AI specialist. Produces ethereal micro-nature visuals, luxury packaging bloom animations, and slow-motion organic beauty spots.",
        "specializations": ["Botanical AI", "Cosmetic Commercials", "Organic Motion"],
        "skills": ["Procedural Petal Growth", "Soft Caustics", "Macro Lighting", "Color Chemistry"],
        "industries": ["Cosmetics", "Fragrance", "Wellness", "Organic Food"],
        "ai_tools": ["Midjourney v6", "Runway Gen-3", "Magnific AI", "Topaz Video AI"],
        "ai_models": ["Midjourney 6.1", "Gen-3 Alpha"],
        "workflow_description": "Botanical growth procedural prompt scheduling with volumetric sub-surface scattering.",
        "experience_years": 4.3,
        "content_types": ["Product Visualization", "Social Video Commercial", "Commercial Stills"],
        "supported_platforms": ["Instagram Reels", "TikTok", "Digital In-Store"],
        "aspect_ratios": ["9:16 (Vertical Reels/TikTok)", "1:1 (Square)"],
        "minimum_budget": 2800.0,
        "maximum_budget": 11500.0,
        "hourly_compute_rate": 50.0,
        "base_model": "Midjourney v6.1 + Runway Gen-3",
        "availability_status": "available",
        "portfolio": [
            {
                "title": "Flora Lumina: Organic Rose Serum",
                "content_type": "Product Visualization",
                "media_path": "https://assets.mixkit.co/videos/preview/mixkit-pink-flowers-in-the-wind-42353-large.mp4",
                "thumbnail_path": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80",
                "aspect_ratio": "9:16",
                "style_tags": ["Botanical Bloom", "Soft Caustics", "Ethereal Glow"],
                "evidence_status": "c2pa_signed"
            }
        ]
    }
]

BRAND_SEEDS = [
    {
        "id": "brand_puma",
        "username": "puma_lab",
        "display_name": "Puma Innovation Lab",
        "avatar_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=100&q=80",
        "bio": "Global athletic and lifestyle innovator testing frontier generative advertising.",
        "brand_name": "Puma Innovation Lab",
        "public_alias": "Puma Innovation Lab",
        "visibility_mode": "public",
        "industry": "Footwear & Athletic Apparel",
        "organization_details": {"hq": "Herzogenaurach, Germany", "vat_id": "DE123456789"}
    },
    {
        "id": "brand_horizon",
        "username": "horizon_ev",
        "display_name": "Horizon Motors",
        "avatar_url": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=100&q=80",
        "bio": "Next-generation electric vehicle manufacturer pioneering autonomous mobility.",
        "brand_name": "Horizon Motors",
        "public_alias": "Horizon Motors",
        "visibility_mode": "public",
        "industry": "Automotive & Clean Energy",
        "organization_details": {"hq": "Stockholm, Sweden", "registration": "SE-556012"}
    },
    {
        "id": "brand_stealth",
        "username": "apex_stealth",
        "display_name": "Project Apex Studio",
        "avatar_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=100&q=80",
        "bio": "Stealth consumer electronics enterprise.",
        "brand_name": "Apex Quantum Robotics Inc.",
        "public_alias": "Project Apex Studio",
        "visibility_mode": "confidential",
        "industry": "Confidential Hardware & Robotics",
        "organization_details": {"legal_name": "Apex Quantum Robotics Inc.", "tax_id": "US-CONFIDENTIAL-992", "nda_required": True}
    }
]

ADMIN_SEED = {
    "id": "admin_master",
    "username": "frame_admin",
    "display_name": "FRAME Platform Administrator",
    "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80",
    "bio": "Chief Security & Moderation Controller.",
    "role": "admin"
}


def seed_database(db: Session):
    """Populates database with 12+ creators, brands, briefs, projects, milestones, and achievements."""
    # Ensure achievement definitions exist
    AchievementEngine.ensure_definitions_exist(db)

    # 1. Seed Admin
    existing_admin = db.query(Profile).filter(Profile.id == ADMIN_SEED["id"]).first()
    if not existing_admin:
        admin_p = Profile(
            id=ADMIN_SEED["id"],
            username=ADMIN_SEED["username"],
            normalized_username=AuthService.normalize_username(ADMIN_SEED["username"]),
            password_hash=AuthService.hash_password("AdminPass2026!"),
            display_name=ADMIN_SEED["display_name"],
            avatar_url=ADMIN_SEED["avatar_url"],
            bio=ADMIN_SEED["bio"],
            role="admin",
            account_status="active"
        )
        db.add(admin_p)

    # 2. Seed Brands
    for b in BRAND_SEEDS:
        existing_b = db.query(Profile).filter(Profile.id == b["id"]).first()
        if not existing_b:
            p = Profile(
                id=b["id"],
                username=b["username"],
                normalized_username=AuthService.normalize_username(b["username"]),
                password_hash=AuthService.hash_password("BrandPass2026!"),
                display_name=b["display_name"],
                avatar_url=b["avatar_url"],
                bio=b["bio"],
                role="brand",
                account_status="active"
            )
            db.add(p)
            bp = BrandProfile(
                user_id=b["id"],
                brand_name=b["brand_name"],
                public_alias=b["public_alias"],
                visibility_mode=b["visibility_mode"],
                industry=b["industry"],
                organization_details=json.dumps(b["organization_details"])
            )
            db.add(bp)

    # 3. Seed Creators & Portfolios & Feed Posts
    for c in CREATOR_SEEDS:
        existing_c = db.query(Profile).filter(Profile.id == c["id"]).first()
        if not existing_c:
            p = Profile(
                id=c["id"],
                username=c["username"],
                normalized_username=AuthService.normalize_username(c["username"]),
                password_hash=AuthService.hash_password("CreatorPass2026!"),
                display_name=c["display_name"],
                avatar_url=c["avatar_url"],
                bio=c["bio"],
                role="creator",
                account_status="active"
            )
            db.add(p)

            cp = CreatorProfile(
                user_id=c["id"],
                specializations=json.dumps(c["specializations"]),
                skills=json.dumps(c["skills"]),
                industries=json.dumps(c["industries"]),
                ai_tools=json.dumps(c["ai_tools"]),
                ai_models=json.dumps(c["ai_models"]),
                workflow_description=c["workflow_description"],
                experience_years=c["experience_years"],
                supported_content_types=json.dumps(c["content_types"]),
                supported_platforms=json.dumps(c["supported_platforms"]),
                aspect_ratios=json.dumps(c["aspect_ratios"]),
                minimum_budget=c["minimum_budget"],
                maximum_budget=c["maximum_budget"],
                hourly_compute_rate=c["hourly_compute_rate"],
                base_model=c["base_model"],
                availability_status=c["availability_status"],
                accepting_projects=True,
                profile_visibility="public"
            )
            db.add(cp)

            # Verification record
            vrec = VerificationRecord(
                user_id=c["id"],
                verification_type="identity_kyc",
                provider_reference=f"DEMO_VERIF_{c['id'].upper()}",
                status="verified",
                is_demo=True,
                verified_at=datetime.now(timezone.utc) - timedelta(days=60)
            )
            db.add(vrec)

            # Portfolio items & Feed posts
            for idx, item in enumerate(c.get("portfolio", [])):
                pi = PortfolioItem(
                    creator_id=c["id"],
                    title=item["title"],
                    description=f"Production case study: {item['title']}",
                    content_type=item["content_type"],
                    media_path=item["media_path"],
                    thumbnail_path=item["thumbnail_path"],
                    skills=json.dumps(c["skills"][:3]),
                    industries=json.dumps(c["industries"][:2]),
                    style_tags=json.dumps(item["style_tags"]),
                    ai_tools=json.dumps(c["ai_tools"][:3]),
                    ai_models=json.dumps(c["ai_models"][:2]),
                    aspect_ratio=item["aspect_ratio"],
                    visibility="public",
                    evidence_status=item["evidence_status"],
                    rights_status="creator_owned",
                    published_at=datetime.now(timezone.utc) - timedelta(days=10 + idx)
                )
                db.add(pi)
                db.flush()

                # Corresponding Feed Post
                fp = FeedPost(
                    creator_id=c["id"],
                    portfolio_item_id=pi.id,
                    caption=f"{item['title']} • Created with {c['base_model']}. #AIFilm #Generative",
                    media_path=item["media_path"],
                    thumbnail_path=item["thumbnail_path"],
                    content_type=item["content_type"],
                    style_tags=json.dumps(item["style_tags"]),
                    ai_tools=json.dumps(c["ai_tools"][:2]),
                    ai_models=json.dumps(c["ai_models"][:2]),
                    visibility="public",
                    moderation_status="approved",
                    published_at=datetime.now(timezone.utc) - timedelta(days=idx * 2)
                )
                db.add(fp)

    db.commit()

    # 4. Seed Creative Briefs
    sample_briefs = [
        {
            "id": "brief_01",
            "brand_id": "brand_puma",
            "title": "Cyber-Puma • 15s High-Energy Neon Sneaker Commercial",
            "objective": "Launch the new futuristic 'Puma Quantum' running shoe with a fast-paced kinetic 15s commercial tailored for TikTok and Reels.",
            "industry": "Footwear",
            "target_audience": "Gen-Z & Sneaker Enthusiasts",
            "deliverables": ["1x 15s 4K Video Master", "1x 9:16 Social Cutdown"],
            "content_types": ["Social Video Commercial"],
            "creative_style": "Cyber-Futurism, Kinetic Neon, Macro Slow-Mo",
            "aspect_ratios": ["9:16 (Vertical Reels/TikTok)"],
            "budget_min": 3500.0,
            "budget_max": 4500.0,
            "currency": "INR",
            "confidentiality_requirements": "public",
            "status": "open"
        },
        {
            "id": "brief_02",
            "brand_id": "brand_horizon",
            "title": "Lucid Horizon • Autonomous EV Nordic Glacier Teaser",
            "objective": "Produce a high-concept 45-second cinematic trailer showing an autonomous EV carving through Nordic glaciers under auroras.",
            "industry": "Automotive",
            "target_audience": "Luxury Automotive Buyers",
            "deliverables": ["1x 45s Cinema 4K Master"],
            "content_types": ["AI Short Film"],
            "creative_style": "Cinematic Photorealism, Anamorphic Glaciers, Volumetric Aurora",
            "aspect_ratios": ["16:9 (Cinema / YouTube 4K)"],
            "budget_min": 6000.0,
            "budget_max": 7500.0,
            "currency": "INR",
            "confidentiality_requirements": "public",
            "status": "open"
        },
        {
            "id": "brief_03",
            "brand_id": "brand_stealth",
            "title": "Project Apex • Unannounced Bipedal Home Companion Teaser",
            "objective": "CONFIDENTIAL: 30s teaser demonstration of biomimetic robotic locomotion. Non-disclosure agreement enforced.",
            "industry": "Robotics",
            "target_audience": "Enterprise Partners & Investors",
            "deliverables": ["1x 30s Confidential Master"],
            "content_types": ["Social Video Commercial"],
            "creative_style": "Monolithic Minimalist, Studio Caustics",
            "aspect_ratios": ["16:9 (Cinema)"],
            "budget_min": 8000.0,
            "budget_max": 12000.0,
            "currency": "INR",
            "confidentiality_requirements": "confidential",
            "status": "open"
        }
    ]

    for sb in sample_briefs:
        existing_sb = db.query(CreativeBrief).filter(CreativeBrief.id == sb["id"]).first()
        if not existing_sb:
            cb = CreativeBrief(
                id=sb["id"],
                brand_id=sb["brand_id"],
                title=sb["title"],
                objective=sb["objective"],
                industry=sb["industry"],
                target_audience=sb["target_audience"],
                deliverables=json.dumps(sb["deliverables"]),
                content_types=json.dumps(sb["content_types"]),
                creative_style=sb["creative_style"],
                aspect_ratios=json.dumps(sb["aspect_ratios"]),
                budget_min=sb["budget_min"],
                budget_max=sb["budget_max"],
                currency=sb["currency"],
                confidentiality_requirements=sb["confidentiality_requirements"],
                status=sb["status"]
            )
            db.add(cb)

    db.commit()

    # 5. Seed an active project, milestones, conversation, and demo financial transaction
    existing_proj = db.query(Project).filter(Project.id == "proj_seed_01").first()
    if not existing_proj:
        proj = Project(
            id="proj_seed_01",
            brand_id="brand_puma",
            creator_id="creator_05",
            brief_id="brief_01",
            title="Cyber-Puma Commercial Kickoff",
            status="in_production",
            visibility_mode="public",
            budget_amount=4500.0,
            currency="INR",
            start_date=datetime.now(timezone.utc) - timedelta(days=4),
            deadline=datetime.now(timezone.utc) + timedelta(days=3)
        )
        db.add(proj)
        db.commit()

        # Milestones
        m1 = ProjectMilestone(
            project_id="proj_seed_01",
            title="Milestone 1: 30% Upfront Compute & Style Lock",
            percentage=30,
            amount=1350.0,
            status="approved",
            completed_at=datetime.now(timezone.utc) - timedelta(days=3)
        )
        m2 = ProjectMilestone(
            project_id="proj_seed_01",
            title="Milestone 2: 40% Rough Cut & Audio Sync",
            percentage=40,
            amount=1800.0,
            status="in_progress"
        )
        m3 = ProjectMilestone(
            project_id="proj_seed_01",
            title="Milestone 3: 30% Final 4K Master & C2PA Provenance Seal",
            percentage=30,
            amount=1350.0,
            status="pending"
        )
        db.add_all([m1, m2, m3])
        db.commit()

        # Conversation & Messages
        conv = Conversation(
            id="conv_proj_01",
            created_by="brand_puma",
            project_id="proj_seed_01",
            conversation_type="project"
        )
        db.add(conv)
        db.commit()

        db.add_all([
            ConversationParticipant(conversation_id=conv.id, user_id="brand_puma"),
            ConversationParticipant(conversation_id=conv.id, user_id="creator_05")
        ])

        db.add_all([
            Message(
                conversation_id=conv.id,
                sender_id="brand_puma",
                body="Welcome Julian! Excited to see the initial ComfyUI seed tests for the Puma Quantum shoe.",
                created_at=datetime.now(timezone.utc) - timedelta(days=4)
            ),
            Message(
                conversation_id=conv.id,
                sender_id="creator_05",
                body="Thanks! I've loaded the liquid neon LoRA and locked our camera dolly trajectory. Drafting initial 4-second test render now.",
                created_at=datetime.now(timezone.utc) - timedelta(days=3)
            )
        ])

        # Transaction & Payout Demo Record
        tx = Transaction(
            id="tx_seed_01",
            project_id="proj_seed_01",
            brand_id="brand_puma",
            creator_id="creator_05",
            gross_amount=4500.0,
            platform_fee=450.0,
            net_amount=4050.0,
            currency="INR",
            status="demo_completed",
            provider_reference="DEMO_STRIPE_CH_9921"
        )
        db.add(tx)
        db.commit()

        payout = PayoutRecord(
            id="payout_seed_01",
            creator_id="creator_05",
            transaction_id="tx_seed_01",
            amount=4050.0,
            currency="INR",
            status="demo_settled",
            provider_reference="DEMO_PAYOUT_9921"
        )
        db.add(payout)

        # Seed historical trust events for Julian Mercer
        for i in range(5):
            te = TrustEvent(
                creator_id="creator_05",
                project_id=f"hist_proj_{i}",
                event_type="project_completed_on_time",
                event_status="verified",
                evidence_reference=f"Delivered on time with C2PA seal (Demo Project #{i+1})"
            )
            db.add(te)

        db.commit()

    # Evaluate achievements for all creators
    for c in CREATOR_SEEDS:
        AchievementEngine.evaluate_and_award_user(db, c["id"])

    print(f"Seed database successfully completed! {len(CREATOR_SEEDS)} creators, {len(BRAND_SEEDS)} brands, briefs, projects seeded.")
