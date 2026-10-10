"""
Seed data for AuraForge Marketplace.
Rich creator profiles, portfolios, tools, skills, verification signals,
brand creative briefs, and pre-computed 1024-d style vectors.
"""

from typing import List, Dict, Any
import numpy as np

def generate_deterministic_vector(seed_val: int, dim: int = 1024) -> List[float]:
    """Generates a normalized 1024-d unit vector for deterministic multi-modal simulation."""
    rng = np.random.default_rng(seed_val)
    raw = rng.standard_normal(dim)
    norm = np.linalg.norm(raw)
    return (raw / norm).tolist()

CREATORS_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "creator_01",
        "name": "Elena Rostova",
        "handle": "@elena_arch",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
        "specialty": "Cyber-Brutalist Architecture & Sci-Fi Environments",
        "bio": "Lead visual architect previously at Foster+Partners. Fine-tuned custom LoRA stacks for monolithic neo-tokyo structures with dynamic volumetrics.",
        "rating": 4.98,
        "completed_projects": 34,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "COMMERCIAL_NON_BRANDED",
        "human_likeness": False,
        "hourly_compute_rate": 45.0,
        "base_model": "SDXL Base 1.0 + Custom Brutalist LoRA v3",
        "tools": ["ComfyUI", "SDXL Base 1.0", "Custom LoRA v3", "Topaz Gigapixel AI", "ControlNet Depth"],
        "skills": ["LoRA Fine-Tuning", "Volumetric Fog Rendering", "ComfyUI Node DAG", "Architectural CAD Infusion", "Octane Shading"],
        "content_types": ["3D Architectural Render", "Concept Art", "Commercial Stills", "Matte Painting"],
        "supported_aspect_ratios": ["16:9 (Cinema)", "21:9 (Ultrawide)", "1:1 (Square)", "4:5 (Social)"],
        "commercial_terms": ["Full Commercial Buyout", "Non-Exclusive Commercial", "C2PA Provenance Signed"],
        "verification_signals": {
            "verified_tools": ["ComfyUI Certified Expert", "SDXL Specialist"],
            "verified_workflow": "AST-Audited Deterministic DAG (SHA-256)",
            "past_work": "34 Projects • 4.98 Rating • 100% On-Time Delivery",
            "trust_badge": "Top Rated Enterprise Creator"
        },
        "style_tags": ["Brutalism", "Cyberpunk", "Monolithic", "Volumetric Fog", "Octane Render", "Raytraced"],
        "vector_embedding": generate_deterministic_vector(101),
        "radar_scores": {
            "palette": 96,
            "lighting": 94,
            "structure": 98,
            "originality": 92,
            "prompt_complexity": 89
        },
        "sample_works": [
            {
                "id": "work_01_1",
                "title": "Neo-Megastructure Atrium 07",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-9921-ELN",
                "sha256": "4a7d189cf6e2410a8d6728c312781b0f56a31c5905d45d8f619b014389df941c",
                "category": "Architecture",
                "aspect_ratio": "16:9",
                "tools_used": ["ComfyUI", "SDXL Base 1.0", "Brutalist LoRA v3"],
                "prompt": "monolithic concrete megastructure in hyper-dense neon mist, brutalist scale, raw concrete textures, anamorphic lens, 8k"
            },
            {
                "id": "work_01_2",
                "title": "Quantum Citadel Transit Hub",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-9922-ELN",
                "sha256": "8f2190bb59e421cd7a06a201bcf51772183c51ef67923491ba681283e1c64491",
                "category": "Architecture",
                "aspect_ratio": "16:9",
                "tools_used": ["ComfyUI", "ControlNet Depth", "Topaz Gigapixel"],
                "prompt": "futuristic multi-level transit terminal, glowing cobalt rail conduits, rainy atmosphere, hyperdetailed raytraced reflections"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "3": {"class_type": "KSampler", "inputs": {"seed": 89412491, "steps": 35, "cfg": 7.5, "sampler_name": "euler_ancestral", "scheduler": "karras", "denoise": 1.0}},
                "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sdxl_brutalist_v3.safetensors"}},
                "5": {"class_type": "LoraLoader", "inputs": {"lora_name": "megastructure_geometry_v2.safetensors", "strength_model": 0.85, "strength_clip": 0.85}},
                "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "monolithic concrete megastructure in hyper-dense neon mist, brutalist scale, raw concrete textures, anamorphic lens, 8k"}},
                "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "deformed, low quality, oversaturated, blurry, cartoon, flat shading"}},
                "8": {"class_type": "VAEDecode", "inputs": {}},
                "9": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Elena Rostova", "license": "Commercial-Exclusive", "embed_dct_watermark": True}}
            }
        }
    },
    {
        "id": "creator_05",
        "name": "Julian Mercer",
        "handle": "@mercer_films",
        "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
        "specialty": "AI Filmmaking, Neural VFX & Runway Gen-3 Directing",
        "bio": "Award-winning generative filmmaker and director. Directs full cinematic AI commercials, music videos, and brand teasers with temporal consistency, camera motion control, and multi-track audio sync.",
        "rating": 4.99,
        "completed_projects": 51,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "COMMERCIAL_NON_BRANDED",
        "human_likeness": False,
        "hourly_compute_rate": 75.0,
        "base_model": "Runway Gen-3 Alpha + Luma Ray 2 + Custom Motion LoRA",
        "tools": ["Runway Gen-3 Alpha", "Kling AI", "Luma Dream Machine", "ComfyUI AnimateDiff", "ElevenLabs", "Topaz Video AI"],
        "skills": ["Temporal Consistency", "Camera Motion Control", "Neural Lip Sync", "Multi-Pass Video Upscaling", "Cinematic Prompt Crafting", "Audio Sync"],
        "content_types": ["AI Short Film", "Social Video Commercials", "3D Kinetic Motion", "Music Videos", "Brand Teasers"],
        "supported_aspect_ratios": ["16:9 (Cinema)", "9:16 (Vertical Reels/TikTok)", "2.39:1 (Anamorphic)"],
        "commercial_terms": ["Full Buyout & Global Broadcast Rights", "Social Media Commercial License", "C2PA v2.1 Chain-of-Custody"],
        "verification_signals": {
            "verified_tools": ["Runway Certified Director", "Topaz Enterprise Upscaler"],
            "verified_workflow": "Multi-Pass Seed-Locked Video DAG (Runway + AnimateDiff)",
            "past_work": "51 Film Projects • 4.99 Rating • Cannes / Tribeca X Finalist",
            "trust_badge": "Verified AI Film Director"
        },
        "style_tags": ["Cinematic", "Sci-Fi Film", "Anamorphic", "Hyperrealism", "Dynamic Motion", "Color Graded"],
        "vector_embedding": generate_deterministic_vector(505),
        "radar_scores": {
            "palette": 98,
            "lighting": 97,
            "structure": 95,
            "originality": 99,
            "prompt_complexity": 96
        },
        "sample_works": [
            {
                "id": "work_05_1",
                "title": "Chrono-Drift: Electric Supercar Reveal",
                "type": "video",
                "image_url": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=800&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-5501-JLM",
                "sha256": "6b72a94f0923e198b1029c8374d9201a09283746592817263548910293847561",
                "category": "AI Commercial Video",
                "aspect_ratio": "16:9",
                "tools_used": ["Runway Gen-3 Alpha", "Topaz Video AI", "ComfyUI"],
                "prompt": "cinematic drone orbit shot of a matte-black electric hypercar drifting through neon soaked midnight rain, photorealistic water droplet reflections, 35mm film grain"
            },
            {
                "id": "work_05_2",
                "title": "Sub-Zero Neon Sneakers TikTok 15s",
                "type": "video",
                "image_url": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-5502-JLM",
                "sha256": "4c982310b987261a872648930192837461928374619283746192837461928374",
                "category": "Social Video Commercial",
                "aspect_ratio": "9:16",
                "tools_used": ["Kling AI", "Runway Gen-3", "ElevenLabs"],
                "prompt": "dynamic vertical fast-whip camera pan, floating neon cyan sneakers bursting through frozen glass water crystals, bass drop rhythm, high kinetic energy"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "VideoPromptSequencer", "inputs": {"camera_motion": "orbit_clockwise_fast", "speed_multiplier": 1.25}},
                "2": {"class_type": "RunwayGen3Connector", "inputs": {"motion_brush_intensity": 7, "fps": 24, "seed": 9928174}},
                "3": {"class_type": "TopazVideoEnhancer", "inputs": {"target_resolution": "4K_ProRes", "model": "Proteus_v4"}},
                "4": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Julian Mercer", "license": "Global-Broadcast-Commercial", "embed_dct_watermark": True}}
            }
        }
    },
    {
        "id": "creator_06",
        "name": "Maya Chen",
        "handle": "@maya_virtual3d",
        "avatar": "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=200&q=80",
        "specialty": "3D Character Animation, Virtual Influencers & UGC Avatars",
        "bio": "Pioneering virtual humans and AI character animators for brands. Specializes in multi-angle identity lock, audio-driven lip sync, and hyper-engaging vertical TikTok video ads.",
        "rating": 4.96,
        "completed_projects": 38,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "HUMAN_LIKENESS_EDITORIAL",
        "human_likeness": True,
        "model_release_verified": True,
        "model_release_ref": "RELEASE-2026-MC-88192",
        "hourly_compute_rate": 55.0,
        "base_model": "FLUX.1 Dev + Hedra Character Engine + FaceID Lock",
        "tools": ["Hedra AI", "Kling AI", "Flux.1 Dev", "ComfyUI FaceID", "ElevenLabs", "Blender"],
        "skills": ["Facial Motion Capture AI", "Multi-Angle Consistency", "Hyperreal Skin Shading", "Audio-Driven Lip Sync", "Vertical Video Framing"],
        "content_types": ["UGC Video Ads", "Virtual Brand Ambassador", "3D Character Animation", "Social Video"],
        "supported_aspect_ratios": ["9:16 (Vertical Reels/TikTok)", "1:1 (Square)", "16:9 (Display)"],
        "commercial_terms": ["Full Commercial Social Rights", "Model Likeness Clearances", "California Civil Code §3344 Compliant"],
        "verification_signals": {
            "verified_tools": ["Hedra Character Certified", "FaceID Consistency Master"],
            "verified_workflow": "Dual-Latent Facial Mesh Lock Pipeline",
            "past_work": "38 Commercials • 4.96 Rating • 100% Brand Safe Clearances",
            "trust_badge": "Verified Virtual Human Specialist"
        },
        "style_tags": ["Virtual Influencer", "UGC Style", "Photorealistic Avatar", "Lip-Synced", "Gen-Z Commercial"],
        "vector_embedding": generate_deterministic_vector(606),
        "radar_scores": {
            "palette": 94,
            "lighting": 96,
            "structure": 97,
            "originality": 95,
            "prompt_complexity": 93
        },
        "sample_works": [
            {
                "id": "work_06_1",
                "title": "Aria AI: Virtual Skincare Ambassador 9:16",
                "type": "video",
                "image_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=800&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-6601-MYC",
                "sha256": "8a91283746192837461928374619283746192837461928374619283746192837",
                "category": "Virtual Influencer UGC",
                "aspect_ratio": "9:16",
                "tools_used": ["Flux.1 Dev", "Hedra AI", "ElevenLabs"],
                "prompt": "hyper-realistic virtual spokesperson testing serum drops on cheek, natural sunlight window reflection, perfect phoneme lip-sync"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "flux1_dev_character.safetensors"}},
                "2": {"class_type": "FaceIDConsistencyLock", "inputs": {"identity_reference": "aria_model_canonical.safetensors", "weight": 0.95}},
                "3": {"class_type": "HedraAudioLipSync", "inputs": {"audio_track": "brand_hook_voice.wav", "smoothing": 0.85}},
                "4": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Maya Chen", "license": "Commercial-Social-Exclusive"}}
            }
        }
    },
    {
        "id": "creator_02",
        "name": "Marcus Vance",
        "handle": "@vance_editorial",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
        "specialty": "Haute Couture Editorial & Hyper-Real Human Portraits",
        "bio": "Former fashion photographer and photorealism prompt engineer. Holds legal Model Releases for synthetic digital twin likenesses with full commercial indemnification.",
        "rating": 4.95,
        "completed_projects": 42,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "HUMAN_LIKENESS_EDITORIAL",
        "human_likeness": True,
        "model_release_verified": True,
        "model_release_ref": "RELEASE-2026-MV-09418",
        "hourly_compute_rate": 60.0,
        "base_model": "FLUX.1 Schnell + Studio Lighting LoRA",
        "tools": ["FLUX.1 Schnell", "Flux.1 Dev", "ComfyUI", "Magnific AI", "Photoshop Generative"],
        "skills": ["Studio Lighting", "Skin Texture Coherence", "Model Release Gating", "Haute Couture Styling", "High-Resolution Inpainting"],
        "content_types": ["Editorial Portrait", "Fashion Campaign Stills", "Commercial Stills", "Lookbooks"],
        "supported_aspect_ratios": ["4:5 (Instagram)", "9:16 (Vertical)", "1:1 (Square)", "16:9 (Landscape)"],
        "commercial_terms": ["California Civil Code §3344 Compliant", "Full Model Release Included", "Commercial Editorial"],
        "verification_signals": {
            "verified_tools": ["Flux.1 Dev Master", "Model Release Auditor"],
            "verified_workflow": "Release-Locked Synthetic DAG",
            "past_work": "42 Projects • 4.95 Rating • Legal Indemnity Guaranteed",
            "trust_badge": "Verified Editorial Specialist"
        },
        "style_tags": ["Haute Couture", "Studio Lighting", "Skin Texture", "Vogue Aesthetic", "Cinematic Portrait"],
        "vector_embedding": generate_deterministic_vector(202),
        "radar_scores": {
            "palette": 93,
            "lighting": 99,
            "structure": 90,
            "originality": 95,
            "prompt_complexity": 94
        },
        "sample_works": [
            {
                "id": "work_02_1",
                "title": "Ethereal Glass Garment Portrait",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-8831-MVC",
                "sha256": "3d5961e938f2191bb81e771488c91a01174955b2049e6f3918a22bc70817b189",
                "category": "Editorial Portrait",
                "aspect_ratio": "4:5",
                "tools_used": ["FLUX.1 Schnell", "ComfyUI", "Magnific AI"],
                "prompt": "haute couture editorial portrait, studio Rembrandt rim lighting, high skin pore fidelity, 85mm f/1.4 lens, natural catchlights"
            },
            {
                "id": "work_02_2",
                "title": "Obsidian Silk Studio Session",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-8832-MVC",
                "sha256": "9b12854cf0193188e67a91204cbf8a12401889a712395bcf827103a49281e012",
                "category": "Editorial Portrait",
                "aspect_ratio": "4:5",
                "tools_used": ["Flux.1 Dev", "Studio Softbox LoRA"],
                "prompt": "flowing obsidian silk fabric draped over model, reflective dark glass floor, chiaroscuro lighting, luxury perfume campaign look"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "flux1_dev_fp8.safetensors"}},
                "2": {"class_type": "LoraLoader", "inputs": {"lora_name": "studio_softbox_cinematic_v4.safetensors", "strength_model": 0.90}},
                "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "haute couture editorial portrait, studio Rembrandt rim lighting, high skin pore fidelity, 85mm f/1.4 lens, natural catchlights, model release confirmed"}},
                "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "plastic skin, airbrushed, oversmoothed, doll-like, bad eyes, extra limbs"}},
                "5": {"class_type": "KSampler", "inputs": {"seed": 7329104, "steps": 40, "cfg": 6.0, "sampler_name": "dpmpp_2m_sde", "scheduler": "exponential"}},
                "6": {"class_type": "VAEDecode", "inputs": {}},
                "7": {"class_type": "ModelReleaseBinder", "inputs": {"release_id": "RELEASE-2026-MV-09418", "indemnity_verified": True}},
                "8": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Marcus Vance", "license": "Editorial-Commercial-TierB"}}
            }
        }
    },
    {
        "id": "creator_03",
        "name": "Kaito Tanaka",
        "handle": "@kaito_synthetics",
        "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80",
        "specialty": "Neo-Cyber Anime & Stylized Game Concept Art",
        "bio": "Anime & mecha concept designer with 10+ years in gaming. Trains multi-resolution ControlNets for precision lineart and cell-shaded aesthetic consistency.",
        "rating": 4.92,
        "completed_projects": 29,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "COMMERCIAL_NON_BRANDED",
        "human_likeness": False,
        "hourly_compute_rate": 38.0,
        "base_model": "Animagine XL 3.1 + Mecha ControlNet",
        "tools": ["Animagine XL 3.1", "ControlNet v1.1", "ComfyUI", "Midjourney v6", "Photoshop"],
        "skills": ["ControlNet Lineart", "Cell-Shading", "Dynamic Action Posing", "Character Turnarounds", "Mecha Hard-Surface"],
        "content_types": ["Concept Art", "Anime Key Visuals", "Character Sheets", "2D/3D Animation Keys"],
        "supported_aspect_ratios": ["16:9 (Cinema)", "4:3 (Classic)", "1:1 (Square)"],
        "commercial_terms": ["Commercial-Standard", "Derivative Rights Allowed", "Full IP Transfer"],
        "verification_signals": {
            "verified_tools": ["ControlNet Master", "Anime Diffusion Specialist"],
            "verified_workflow": "Multi-ControlNet Consistency DAG",
            "past_work": "29 Projects • 4.92 Rating • 99% Repeat Clients",
            "trust_badge": "Verified Game Artist"
        },
        "style_tags": ["Neo-Anime", "Mecha", "Cell-Shading", "Dynamic Action", "Cyber-Samurai", "Concept Art"],
        "vector_embedding": generate_deterministic_vector(303),
        "radar_scores": {
            "palette": 97,
            "lighting": 89,
            "structure": 94,
            "originality": 96,
            "prompt_complexity": 91
        },
        "sample_works": [
            {
                "id": "work_03_1",
                "title": "Valkyrie Exosuit Wing 04",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-7711-KTN",
                "sha256": "1a9c37e1920875bca12093847b019842f1a9b240182746bc9201948ba9e10283",
                "category": "Concept Art",
                "aspect_ratio": "16:9",
                "tools_used": ["Animagine XL 3.1", "ControlNet Lineart"],
                "prompt": "1girl, cyber-samurai, mechanized katana, glowing holographic visor, neon rain reflections, dynamic action pose, masterpiece lineart"
            },
            {
                "id": "work_03_2",
                "title": "Cyber-Ronin Rain Alley",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-7712-KTN",
                "sha256": "7c192840918374bb910394857102948bca910482910394857102948bca910482",
                "category": "Concept Art",
                "aspect_ratio": "16:9",
                "tools_used": ["ComfyUI", "Midjourney v6"],
                "prompt": "cyber-ronin standing in drenched neo-shinjuku alleyway, glowing rain ripples, cel-shaded anime aesthetic"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "animagine_xl_v31.safetensors"}},
                "2": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "control_v11p_sd15_lineart.pth"}},
                "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "1girl, cyber-samurai, mechanized katana, glowing holographic visor, neon rain reflections, dynamic action pose, masterpiece lineart"}},
                "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "western comic, 3d render, photorealistic, bad anatomy, lowres"}},
                "5": {"class_type": "KSampler", "inputs": {"seed": 4920193, "steps": 30, "cfg": 8.0, "sampler_name": "euler", "scheduler": "normal"}},
                "6": {"class_type": "VAEDecode", "inputs": {}},
                "7": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Kaito Tanaka", "license": "Commercial-Standard"}}
            }
        }
    },
    {
        "id": "creator_04",
        "name": "Astrid Lindholm",
        "handle": "@nordic_biomorphic",
        "avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80",
        "specialty": "Biomorphic Product Design & Organic Ceramics",
        "bio": "Industrial designer blending Scandinavian minimalism with generative cellular automata. Specialized in C2PA-provenanced consumer product prototypes.",
        "rating": 4.97,
        "completed_projects": 19,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "COMMERCIAL_NON_BRANDED",
        "human_likeness": False,
        "hourly_compute_rate": 50.0,
        "base_model": "SDXL + Parametric Surface LoRA",
        "tools": ["SDXL Base 1.0", "ComfyUI", "Blender + AI Nodes", "Parametric LoRA"],
        "skills": ["Parametric Modeling", "Texture Synthesis", "Product Lighting", "C2PA Provenance Stamping", "CAD Alignment"],
        "content_types": ["Product Visualization", "Industrial Design Renders", "Packaging Mockups"],
        "supported_aspect_ratios": ["1:1 (Square)", "16:9 (Cinema)", "4:5 (Social)"],
        "commercial_terms": ["Full Buyout & Manufacturing Rights", "Exclusive Commercial License"],
        "verification_signals": {
            "verified_tools": ["Industrial Design Verified", "C2PA Enterprise Signer"],
            "verified_workflow": "Parametric VAE Pipeline",
            "past_work": "19 Projects • 4.97 Rating • Top Agency Vendor",
            "trust_badge": "Verified Product Designer"
        },
        "style_tags": ["Scandinavian", "Biomorphic", "Minimalist", "Ceramic Textures", "Industrial Design"],
        "vector_embedding": generate_deterministic_vector(404),
        "radar_scores": {
            "palette": 95,
            "lighting": 97,
            "structure": 96,
            "originality": 94,
            "prompt_complexity": 88
        },
        "sample_works": [
            {
                "id": "work_04_1",
                "title": "Cellular Matte Porcelain Vessel",
                "type": "image",
                "image_url": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=800&q=80",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "AF-6621-AST",
                "sha256": "5c91823901928374619283749102938471029384710293847102938471029384",
                "category": "Industrial Design",
                "aspect_ratio": "1:1",
                "tools_used": ["SDXL Base 1.0", "Parametric LoRA"],
                "prompt": "scandinavian minimalist biomorphic ceramic vase, matte speckled finish, neutral studio lighting, sharp shadow gradient, 8k"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sdxl_base_1.0.safetensors"}},
                "2": {"class_type": "LoraLoader", "inputs": {"lora_name": "biomorphic_ceramics_v1.safetensors", "strength_model": 0.8}},
                "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "scandinavian minimalist biomorphic ceramic vase, matte speckled finish, neutral studio lighting, sharp shadow gradient, 8k"}},
                "4": {"class_type": "KSampler", "inputs": {"seed": 9182736, "steps": 32, "cfg": 7.0, "sampler_name": "dpmpp_2m", "scheduler": "karras"}},
                "5": {"class_type": "VAEDecode", "inputs": {}},
                "6": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Astrid Lindholm", "license": "Commercial-Exclusive"}}
            }
        }
    },
    {
        "id": "creator_07",
        "name": "Aarav Patel",
        "handle": "@aarav_reels",
        "avatar": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=200&q=80",
        "specialty": "Birthday, Wedding & Social Event Reels Video Editor",
        "bio": "Senior video editor & colorist specializing in short-form cinematic celebration montages, event highlight reels, and music-driven social storytelling. Transforms raw smartphone clips into luxury film-grade reels.",
        "location": "🇮🇳 Mumbai, India",
        "availability": "Available",
        "response_time": "Replies in 1h",
        "rating": 4.97,
        "completed_projects": 64,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "COMMERCIAL_NON_BRANDED",
        "human_likeness": True,
        "hourly_compute_rate": 35.0,
        "hourly_inr": 3000.0,
        "min_project_inr": 5000.0,
        "min_project_usd": 60.0,
        "base_model": "Premiere Pro + Topaz Video AI + DaVinci Resolve",
        "tools": ["Premiere Pro", "CapCut Pro", "Topaz Video AI", "Midjourney v6", "DaVinci Resolve"],
        "skills": ["Emotional Pacing", "Color Grading", "Beat Sync", "Sound Design", "Kinetic Captions", "Video Upscaling"],
        "content_types": ["Birthday / Event Montage", "Social Video Commercial", "UGC Video Ads", "Wedding Reels"],
        "supported_aspect_ratios": ["9:16 (Vertical Reels/TikTok)", "16:9 (Cinema)", "1:1 (Square)", "4:5 (Social)"],
        "commercial_terms": ["Personal & Commercial Digital Use", "Full Non-Exclusive Rights", "Music License Cleared"],
        "verification_signals": {
            "verified_tools": ["Adobe Certified Video Editor", "Topaz Video Upscaling Pro"],
            "verified_workflow": "Multi-Camera Speed-Ramped Timeline Pipeline",
            "past_work": "64 Event Projects • 4.97 Rating • 100% 48-Hour Delivery",
            "trust_badge": "Top Rated Event Reels Editor"
        },
        "style_tags": ["Cinematic Nostalgia", "Warm Kodachrome", "Fast Cuts", "Emotional Beat-Sync", "Luxury Montage"],
        "vector_embedding": generate_deterministic_vector(707),
        "radar_scores": {
            "palette": 95,
            "lighting": 96,
            "structure": 98,
            "originality": 93,
            "prompt_complexity": 90
        },
        "sample_works": [
            {
                "id": "work_07_1",
                "title": "Cinematic Birthday & Event Celebration Reel (30s)",
                "type": "video",
                "image_url": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?auto=format&fit=crop&w=800&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "CS-7701-ARV",
                "sha256": "3e91029384756102938475610293847561029384756102938475610293847561",
                "category": "Birthday & Event",
                "aspect_ratio": "9:16",
                "tools_used": ["Premiere Pro", "CapCut Pro", "Topaz Video AI"],
                "prompt": "vintage Kodachrome 35mm film grain, 30s celebration montage, speed-ramped emotional transitions, warm amber bokeh"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "VideoCutSequencer", "inputs": {"fps": 30, "sync_bpm": 128}},
                "2": {"class_type": "ColorGradeLUTLoader", "inputs": {"lut_name": "warm_kodachrome_cinematic.cube"}},
                "3": {"class_type": "TopazVideoEnhancer", "inputs": {"target_resolution": "4K_ProRes", "model": "Proteus_v4"}},
                "4": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Aarav Patel", "license": "Commercial-Social"}}
            }
        }
    },
    {
        "id": "creator_08",
        "name": "Rohan Verma",
        "handle": "@rohan_motion",
        "avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=200&q=80",
        "specialty": "High-Velocity Commercial & Food Reels Editor",
        "bio": "Viral social media video editor for D2C brands, cafes, and hospitality. Master of kinetic speed ramping, punchy audio Foley design, and motion graphics hook retention.",
        "location": "🇮🇳 Bengaluru, India",
        "availability": "Available",
        "response_time": "Replies in 30m",
        "rating": 4.95,
        "completed_projects": 48,
        "verified": True,
        "c2pa_certified": True,
        "compliance_tier": "COMMERCIAL_NON_BRANDED",
        "human_likeness": True,
        "hourly_compute_rate": 30.0,
        "hourly_inr": 2500.0,
        "min_project_inr": 4500.0,
        "min_project_usd": 55.0,
        "base_model": "DaVinci Resolve Studio + After Effects + Runway Gen-3",
        "tools": ["DaVinci Resolve", "After Effects", "Soundly", "Runway Gen-3 Alpha"],
        "skills": ["Speed Ramps", "Sound Effects", "Dynamic Captions", "Color Grading", "Hook Optimization"],
        "content_types": ["Social Video Commercial", "UGC Video Ads", "Product Visualization"],
        "supported_aspect_ratios": ["9:16 (Vertical Reels/TikTok)", "1:1 (Square)", "16:9 (Cinema)"],
        "commercial_terms": ["Full Commercial Rights", "Paid Social Ads Ready"],
        "verification_signals": {
            "verified_tools": ["DaVinci Resolve Certified", "Motion Design Specialist"],
            "verified_workflow": "Audio-Reactive Dynamic Zoom Cut Pipeline",
            "past_work": "48 Commercial Reels • 4.95 Rating • 2M+ Aggregate Views",
            "trust_badge": "Verified Social Reels Editor"
        },
        "style_tags": ["Fast Paced", "Punchy Sound", "Animated Captions", "Viral Hook", "Street Food & D2C"],
        "vector_embedding": generate_deterministic_vector(808),
        "radar_scores": {
            "palette": 94,
            "lighting": 95,
            "structure": 97,
            "originality": 96,
            "prompt_complexity": 91
        },
        "sample_works": [
            {
                "id": "work_08_1",
                "title": "Fast-Paced Cafe & Street Food Reel Edit (25s)",
                "type": "video",
                "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
                "c2pa_status": "VERIFIED_AUTHENTIC",
                "watermark_id": "CS-8801-RHV",
                "sha256": "4f91029384756102938475610293847561029384756102938475610293847561",
                "category": "Social Reel",
                "aspect_ratio": "9:16",
                "tools_used": ["DaVinci Resolve", "After Effects", "Soundly"],
                "prompt": "hyper-kinetic coffee pour and street culinary sizzle, whip-pan zooms, punchy foley audio, saturated warm palette"
            }
        ],
        "default_workflow_json": {
            "client_id": "auraforge-runner",
            "nodes": {
                "1": {"class_type": "KineticAudioSyncNode", "inputs": {"transient_sensitivity": 0.85}},
                "2": {"class_type": "AfterEffectsMogrtInjector", "inputs": {"font": "Outfit-Bold"}},
                "3": {"class_type": "AuraForgeC2PAInjector", "inputs": {"author": "Rohan Verma", "license": "Commercial-Paid-Ads"}}
            }
        }
    }
]

# Seed Brand Briefs capturing all requirements from the hackathon challenge
BRIEFS_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "brief_04",
        "title": "Aarav's 30th Birthday Celebration • Kinetic 30s Reel",
        "brand_name": "Personal Family Commission",
        "brand_logo": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?auto=format&fit=crop&w=100&q=80",
        "objective": "Transform 25 raw phone video clips into an unforgettable 30-second birthday montage for Instagram Reels. Needs emotional music pacing, warm vintage film grain, beat-synced cuts, and animated title overlays.",
        "content_type": "Birthday / Event Montage",
        "style": "Cinematic Nostalgia, Warm Kodachrome, Kinetic Beat-Sync",
        "format_aspect_ratio": "9:16 (Vertical Reels/TikTok)",
        "commercial_use": "Personal & Social Media Rights (Non-Exclusive)",
        "tools_recommended": ["Premiere Pro", "CapCut Pro", "Topaz Video AI", "Midjourney v6"],
        "required_skills": ["Emotional Pacing", "Color Grading", "Beat Sync", "Sound Design"],
        "budget_usd": 65.0,
        "budget_inr": 5000.0,
        "timeline_days": 3,
        "status": "OPEN_FOR_PITCHES",
        "proposals_count": 2,
        "matched_creator_ids": ["creator_07", "creator_08"],
        "milestones": [
            {"phase": "Raw Footage Ingest & Music Beat Selection", "pct": 30, "payout": 1500.0},
            {"phase": "Rough Cut 30s & Sound Effects Pass", "pct": 40, "payout": 2000.0},
            {"phase": "Color Grade, 4K Upscale & Final Export", "pct": 30, "payout": 1500.0}
        ]
    },
    {
        "id": "brief_01",
        "title": "Cyber-Puma • 15s High-Energy Neon Sneaker Commercial",
        "brand_name": "Puma Innovation Lab",
        "brand_logo": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=100&q=80",
        "objective": "Launch the new futuristic 'Puma Quantum' running shoe with a fast-paced, kinetic 15-second commercial tailored for TikTok & Instagram Reels. The sneaker must defy gravity through liquid neon splashes.",
        "content_type": "Social Video Commercial",
        "style": "Cyber-Futurism, Kinetic Neon, Macro Slow-Mo",
        "format_aspect_ratio": "9:16 (Vertical Reels/TikTok)",
        "commercial_use": "Full Commercial Buyout & Global Digital Paid Ads Rights (1 Year)",
        "tools_recommended": ["Runway Gen-3 Alpha", "Kling AI", "Flux.1 Dev", "Topaz Video AI"],
        "required_skills": ["Temporal Consistency", "Camera Motion Control", "Liquid Physics AI", "Multi-Pass Video Upscaling"],
        "budget_usd": 4500.0,
        "timeline_days": 7,
        "status": "OPEN_FOR_PITCHES",
        "proposals_count": 3,
        "matched_creator_ids": ["creator_05", "creator_01"],
        "milestones": [
            {"phase": "LoRA Style & Asset Sandbox Test", "pct": 30, "payout": 1350.0},
            {"phase": "First 15s Cut & Motion Consistency Pass", "pct": 40, "payout": 1800.0},
            {"phase": "Final 4K ProRes & C2PA Provenance Seal", "pct": 30, "payout": 1350.0}
        ]
    },
    {
        "id": "brief_02",
        "title": "Lucid Horizon • Cinematic Teaser for Autonomous EV",
        "brand_name": "Horizon Motors",
        "brand_logo": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=100&q=80",
        "objective": "Produce a high-concept 45-second cinematic trailer showing an autonomous electric vehicle carving through Nordic glaciers under auroras. Needs pristine photorealism and consistent vehicle body reflection.",
        "content_type": "AI Short Film",
        "style": "Cinematic Photorealism, Anamorphic Glaciers, Volumetric Aurora",
        "format_aspect_ratio": "16:9 (Cinema / YouTube 4K)",
        "commercial_use": "Full IP Transfer & Worldwide Broadcast License",
        "tools_recommended": ["Runway Gen-3 Alpha", "ComfyUI AnimateDiff", "Luma Ray 2", "Topaz Video AI"],
        "required_skills": ["Vehicle Body Consistency", "Dynamic Drone Camera Motion", "Lighting Coherence", "Color Grading"],
        "budget_usd": 7200.0,
        "timeline_days": 14,
        "status": "OPEN_FOR_PITCHES",
        "proposals_count": 5,
        "matched_creator_ids": ["creator_05", "creator_01"],
        "milestones": [
            {"phase": "ComfyUI Workflow & Car LoRA Audit", "pct": 30, "payout": 2160.0},
            {"phase": "Raw 1080p Sequence Assembly", "pct": 40, "payout": 2880.0},
            {"phase": "Final 4K Master & C2PA Provenance Lock", "pct": 30, "payout": 2160.0}
        ]
    },
    {
        "id": "brief_03",
        "title": "Aura Luxury Fragrance • 3D Biomorphic Bottle Visuals",
        "brand_name": "Maison d'Aura Paris",
        "brand_logo": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=100&q=80",
        "objective": "Design and render 6 key visual posters showcasing an organic glass perfume bottle encased in crystalline ceramic petals. Needs ultra-crisp studio lighting suitable for luxury billboards and print lookbooks.",
        "content_type": "Product Visualization",
        "style": "Scandinavian Biomorphic Minimal, Glass Refraction, High Fashion",
        "format_aspect_ratio": "4:5 (Instagram / Print)",
        "commercial_use": "Exclusive Worldwide Print & Out-of-Home Billboard Rights",
        "tools_recommended": ["SDXL Base 1.0", "ComfyUI", "Parametric LoRA", "Magnific AI"],
        "required_skills": ["Glass Caustics & Refraction", "Studio Softbox Lighting", "High-Resolution Inpainting"],
        "budget_usd": 3800.0,
        "timeline_days": 5,
        "status": "IN_PRODUCTION",
        "proposals_count": 4,
        "matched_creator_ids": ["creator_04", "creator_02"],
        "milestones": [
            {"phase": "3D Bottle Concept Selection", "pct": 30, "payout": 1140.0},
            {"phase": "High-Res 8K Renders & Variations", "pct": 40, "payout": 1520.0},
            {"phase": "Commercial Release & C2PA Signatures", "pct": 30, "payout": 1140.0}
        ]
    }
]

EMPIRICAL_RESEARCH_DATA = {
    "freelance_displacements": [
        {"domain": "Writing Tasks", "change": -30.37, "color": "#EF4444", "description": "Steepest drop, driven by ChatGPT text automation"},
        {"domain": "Software & Web Dev", "change": -20.62, "color": "#F97316", "description": "Copilot & LLM code generation substitution"},
        {"domain": "Graphic Design", "change": -18.49, "color": "#F59E0B", "description": "Midjourney & DALL-E visual substitution"},
        {"domain": "Visual Creation (Total)", "change": -17.01, "color": "#EAB308", "description": "Aggregate visual automation impact"},
        {"domain": "3D Modeling", "change": -15.57, "color": "#84CC16", "description": "NeRF & 3D generative tool adoption"},
        {"domain": "Engineering (C/Matlab)", "change": -10.42, "color": "#06B6D4", "description": "High barrier, partial algorithmic assistance"}
    ],
    "remaining_job_upsides": [
        {"metric": "Job Skill Complexity Tags", "change": "+2.18%", "trend": "up", "detail": "Employers require multi-tool orchestration instead of single skills"},
        {"metric": "Maximum Client Budgets", "change": "+5.71%", "trend": "up", "detail": "Remaining roles command higher budgets for senior AI supervisors"},
        {"metric": "Bids Per High-Skill Post", "change": "+8.57%", "trend": "up", "detail": "Intense competition among top-tier prompt/model engineers"}
    ],
    "creative_market_dynamics": {
        "platform_expansion": {
            "active_ai_firms_monthly": "+88% (+940 firms/mo)",
            "total_asset_publication": "+78% (+4,900 assets/mo)",
            "total_market_sales": "+39%",
            "product_variety_expansion": "+28% to +35%"
        },
        "non_ai_crowd_out": {
            "traditional_creator_exit_rate": "23% per month",
            "non_ai_asset_creation_drop": "-20% to -22%",
            "per_product_sale_probability": "-4.8% to -5.6% (Search Congestion)"
        },
        "niche_markets": {
            "niche_market_production": "+160% (vs +85% in large markets)",
            "tipping_effect": "Niche categories tipping almost 100% to synthetic generative assets"
        }
    }
}
