-- ============================================================================
-- Seed File: seed.sql
-- Project: CreatorSphere AI
-- Description: Reproducible seed dataset with 12+ diverse fictional creator
--              profiles, portfolio showcases, customer briefs, enquiries,
--              creator interests, and verification signals.
--
-- IMPORTANT NOTICE:
-- All records in this file are strictly FICTIONAL DEMONSTRATION DATA
-- created for college hackathon testing and evaluation purposes.
-- ============================================================================

-- ============================================================================
-- 1. USERS (Customers and Creators)
-- ============================================================================

-- Customers
INSERT INTO public.users (id, email, full_name, role, avatar_url, bio)
VALUES
('00000000-0000-0000-0000-000000000001', 'alice.walker@demo-brand.test', 'Alice Walker', 'customer', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb', 'Brand Director at Peak Athletics looking for high-energy campaign videos.'),
('00000000-0000-0000-0000-000000000002', 'david.chen@lumina-health.test', 'David Chen', 'customer', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d', 'Founder at Lumina Health, hiring 3D animators for medical explainers.'),
('00000000-0000-0000-0000-000000000003', 'sarah.jenkins@nova-fintech.test', 'Sarah Jenkins', 'customer', 'https://images.unsplash.com/photo-1517841905240-472988babdf9', 'Marketing Lead at Nova Fintech sourcing short-form social reels creators.')
ON CONFLICT (id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    avatar_url = EXCLUDED.avatar_url,
    bio = EXCLUDED.bio;

-- Creators (User Accounts)
INSERT INTO public.users (id, email, full_name, role, avatar_url, bio)
VALUES
('00000000-0000-0000-0000-000000000101', 'elena.rostova@demo-creator.test', 'Elena Rostova', 'creator', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2', 'Pioneering AI video artist blending Runway Gen-3 with custom ComfyUI pipelines.'),
('00000000-0000-0000-0000-000000000102', 'marcus.vance@demo-creator.test', 'Marcus Vance', 'creator', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e', 'Commercial editor focused on high-retention storytelling and dynamic sound design.'),
('00000000-0000-0000-0000-000000000103', 'aoi.tanaka@demo-creator.test', 'Aoi Tanaka', 'creator', 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1', '3D motion designer creating stylized animated brand assets in Blender and Cinema 4D.'),
('00000000-0000-0000-0000-000000000104', 'liam.oconnor@demo-creator.test', 'Liam O''Connor', 'creator', 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce', 'Luxury product cinematographer specializing in macro visuals and studio lighting.'),
('00000000-0000-0000-0000-000000000105', 'sofia.reyes@demo-creator.test', 'Sofia Reyes', 'creator', 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2', 'Narrative filmmaker and colorist bringing 35mm film aesthetics to modern digital stories.'),
('00000000-0000-0000-0000-000000000106', 'kavita.patel@demo-creator.test', 'Kavita Patel', 'creator', 'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04', 'Viral short-form specialist crafting high-engagement TikTok and Instagram Reels.'),
('00000000-0000-0000-0000-000000000107', 'julian.dubois@demo-creator.test', 'Julian Dubois', 'creator', 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7', 'Festival and live event videographer delivering same-day recap edits.'),
('00000000-0000-0000-0000-000000000108', 'tariq.almansoor@demo-creator.test', 'Tariq Al-Mansoor', 'creator', 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e', 'AI VFX supervisor exploring generative neural radiance fields and scene synthesis.'),
('00000000-0000-0000-0000-000000000109', 'chloe.martin@demo-creator.test', 'Chloe Martin', 'creator', 'https://images.unsplash.com/photo-1580489944761-15a19d654956', 'SaaS product explainer designer creating isometric UI motion animations.'),
('00000000-0000-0000-0000-000000000110', 'dmitri.volkov@demo-creator.test', 'Dmitri Volkov', 'creator', 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d', 'Analog synth enthusiast and music video editor specializing in retro VHS glitch art.'),
('00000000-0000-0000-0000-000000000111', 'mia.lindqvist@demo-creator.test', 'Mia Lindqvist', 'creator', 'https://images.unsplash.com/photo-1567532939604-b6b5b0db2604', 'Pro FPV drone pilot capturing high-speed aerial tracking and nature fly-throughs.'),
('00000000-0000-0000-0000-000000000112', 'kenji.sato@demo-creator.test', 'Kenji Sato', 'creator', 'https://images.unsplash.com/photo-1501196354995-cbb51c65aaea', 'Unreal Engine 5 environment artist and virtual production director.')
ON CONFLICT (id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    avatar_url = EXCLUDED.avatar_url,
    bio = EXCLUDED.bio;

-- ============================================================================
-- 2. CREATOR PROFILES
-- ============================================================================

INSERT INTO public.creators (
    id, user_id, handle, display_name, tagline, bio,
    skills, tools, styles, content_types,
    indicative_budget_min, indicative_budget_max, currency,
    availability, experience_years, location, website_url,
    rating, total_reviews, is_featured
)
VALUES
(
    '00000000-0000-0000-0001-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '@synthetica_ai', 'Elena Rostova',
    'Next-Gen AI Filmmaker & Generative Video Architect',
    'Specializing in photorealistic AI generation, character consistency, and multimodal video workflows.',
    ARRAY['AI Video Generation', 'Prompt Engineering', 'Runway Gen-3', 'Midjourney', 'ComfyUI'],
    ARRAY['Runway Gen-3', 'Midjourney v6', 'ComfyUI', 'Topaz Video AI', 'DaVinci Resolve'],
    ARRAY['Hyper-realistic', 'Sci-Fi Surrealism', 'Cyberpunk', 'Cinematic'],
    ARRAY['AI Concept', 'Fashion Promo', 'Music Video', 'Brand Film'],
    500.00, 2500.00, 'USD', 'available', 4, 'Berlin, Germany', 'https://synthetica-ai.demo.test',
    4.95, 34, true
),
(
    '00000000-0000-0000-0001-000000000002',
    '00000000-0000-0000-0000-000000000102',
    '@vance_cuts', 'Marcus Vance',
    'High-Retention Video Editor & Sound Alchemist',
    '8+ years editing fast-paced commercial YouTube content, broadcast promos, and dynamic brand campaigns.',
    ARRAY['Fast Pacing Editing', 'Sound Design', 'Color Grading', 'Multicam Sync'],
    ARRAY['Adobe Premiere Pro', 'After Effects', 'DaVinci Resolve Studio', 'Logic Pro'],
    ARRAY['High-Energy', 'Documentary', 'YouTube Retention Focused', 'Commercial'],
    ARRAY['Commercial', 'YouTube Feature', 'Short-form Series', 'Podcast Highlights'],
    300.00, 1500.00, 'USD', 'available', 8, 'Austin, TX', 'https://vancecuts.demo.test',
    4.88, 62, true
),
(
    '00000000-0000-0000-0001-000000000003',
    '00000000-0000-0000-0000-000000000103',
    '@aoi_motion', 'Aoi Tanaka',
    '3D Motion Designer & Stylized Character Animator',
    'Creating colorful, emotive 3D motion graphics that bring brand identities and tech products to life.',
    ARRAY['3D Motion Graphics', 'Character Rigging', 'Cel Animation', 'Logo Animation'],
    ARRAY['Blender', 'Cinema 4D', 'After Effects', 'Octane Render', 'Procreate Dreams'],
    ARRAY['3D Stylized', 'Minimalist Isometric', 'Anime Inspired', 'Abstract Kinetic'],
    ARRAY['Product 3D', 'Logo Stinger', 'Brand Explainer', 'Mobile Game Trailer'],
    800.00, 4000.00, 'USD', 'busy', 6, 'Tokyo, Japan', 'https://aoimotion.demo.test',
    4.92, 45, true
),
(
    '00000000-0000-0000-0001-000000000004',
    '00000000-0000-0000-0000-000000000104',
    '@product_lens', 'Liam O''Connor',
    'Macro Product Cinematographer & Studio Director',
    'Turning everyday consumer products into luxury cinematic experiences through high-speed robot cameras.',
    ARRAY['Macro Product Cinematography', 'Lighting Design', '3D Product CGI', 'Packshot Editing'],
    ARRAY['Sony FX6', 'Cinema 4D', 'Redshift', 'DaVinci Resolve Studio', 'Blender'],
    ARRAY['Luxury Clean', 'Macro Detailed', 'Bold Commercial', 'Minimalist Studio'],
    ARRAY['Product Commercial', 'E-commerce Hero', 'Cosmetics Showcase', 'Beverage Ad'],
    1200.00, 5000.00, 'USD', 'available', 9, 'London, UK', 'https://productlens.demo.test',
    4.98, 51, true
),
(
    '00000000-0000-0000-0001-000000000005',
    '00000000-0000-0000-0000-000000000105',
    '@reyes_cinema', 'Sofia Reyes',
    'Cinematic Narrative Director & Film Colorist',
    'Award-winning short filmmaker offering rich 35mm film emulation, poetic pacing, and emotional depth.',
    ARRAY['Directing', 'Cinematography', 'Anamorphic Framing', 'Film Emulation Color Grading'],
    ARRAY['RED Komodo', 'ARRI Alexa Mini LF', 'DaVinci Resolve Studio', 'Dehancer Pro'],
    ARRAY['35mm Film Aesthetic', 'Moody Cinematic', 'Documentary Narrative', 'Atmospheric'],
    ARRAY['Cinematic Short', 'Brand Documentary', 'Music Video', 'Manifesto Film'],
    2000.00, 8000.00, 'USD', 'available', 10, 'Mexico City, Mexico', 'https://reyescinema.demo.test',
    5.00, 29, true
),
(
    '00000000-0000-0000-0001-000000000006',
    '00000000-0000-0000-0000-000000000106',
    '@viral_reels_lab', 'Kavita Patel',
    'Short-Form Growth Hacker & Viral Reels Producer',
    'Over 100M cumulative views produced for founders, creators, and DTC brands across TikTok and IG.',
    ARRAY['Viral Hook Scripting', 'Kinetic Typography', 'Sound Trending Sync', 'CapCut Pro Wizardry'],
    ARRAY['CapCut Desktop', 'Adobe Premiere Pro', 'After Effects', 'Epidemic Sound'],
    ARRAY['Snappy Viral', 'Gen-Z Aesthetic', 'Edutainment', 'High-Engagement'],
    ARRAY['Social Reel', 'TikTok Native', 'Founder Story', 'UGC Concept'],
    150.00, 800.00, 'USD', 'available', 3, 'Mumbai, India', 'https://viralreels.demo.test',
    4.85, 78, false
),
(
    '00000000-0000-0000-0001-000000000007',
    '00000000-0000-0000-0000-000000000107',
    '@dubois_events', 'Julian Dubois',
    'Live Event & Music Festival Cinematographer',
    'Capturing the heartbeat of music festivals, tech conferences, and luxury corporate galas.',
    ARRAY['Gimbal Operation', 'Low-Light Filming', 'Same-Day Edits', 'Dynamic Speed Ramping'],
    ARRAY['Sony A7S III', 'DJI RS3 Pro', 'Adobe Premiere Pro', 'FilmConvert'],
    ARRAY['Euphoric Festival', 'Corporate Prestige', 'Emotional Highlights', 'Fast-Paced Recap'],
    ARRAY['Event Recap', 'Music Festival Aftermovie', 'Conference Keynote', 'Gala Teaser'],
    1000.00, 3500.00, 'USD', 'busy', 7, 'Paris, France', 'https://duboisevents.demo.test',
    4.91, 41, false
),
(
    '00000000-0000-0000-0001-000000000008',
    '00000000-0000-0000-0000-000000000108',
    '@ai_motioncraft', 'Tariq Al-Mansoor',
    'AI-Assisted Hybrid VFX & Neural Scene Artist',
    'Blending live-action footage with generative neural synthesis and custom ControlNet workflows.',
    ARRAY['Stable Video Diffusion', 'ControlNet', 'NeRF 3D Scene Reconstruction', 'AI Rotoscoping'],
    ARRAY['ComfyUI', 'Luma Dream Machine', 'After Effects', 'Blender', 'EbSynth'],
    ARRAY['Dreamlike Morphing', 'Futuristic Tech', 'Surreal Reality', 'Cyberpunk'],
    ARRAY['VFX Commercial', 'Sci-Fi Music Video', 'AI Transition Stinger', 'Concept Pitch'],
    900.00, 3200.00, 'USD', 'available', 5, 'Dubai, UAE', 'https://tariqmotion.demo.test',
    4.89, 23, false
),
(
    '00000000-0000-0000-0001-000000000009',
    '00000000-0000-0000-0000-000000000109',
    '@chloe_explains', 'Chloe Martin',
    'B2B SaaS Explainer Video & Motion Specialist',
    'Translating complex software architectures and APIs into sleek, crystal-clear 60-second animated explainers.',
    ARRAY['SaaS UI Motion', 'Vector Illustration', 'Voiceover Sync', 'Infographic Animation'],
    ARRAY['After Effects', 'Figma', 'Adobe Illustrator', 'Audition'],
    ARRAY['Tech Clean', 'Playful Flat Design', 'Corporate Minimal', 'Modern Isometric'],
    ARRAY['SaaS Explainer', 'Product Walkthrough', 'Feature Announcement', 'Investor Pitch Video'],
    700.00, 2800.00, 'USD', 'available', 5, 'Toronto, Canada', 'https://chloemartin.demo.test',
    4.96, 54, false
),
(
    '00000000-0000-0000-0001-000000000010',
    '00000000-0000-0000-0000-000000000110',
    '@retro_vhs_lab', 'Dmitri Volkov',
    'Analog VHS Synthesizer & Music Video Visionary',
    'Authentic magnetic tape glitch art, CRT distortion, and retro 80s/90s aesthetic editing.',
    ARRAY['Analog Tape Transfer', 'Glitch Art', 'Film Grain Synthesis', 'Music Video Direction'],
    ARRAY['Sony CRT Monitor', 'VHS Deck', 'Adobe Premiere Pro', 'TouchDesigner', 'DaVinci Resolve'],
    ARRAY['Retro VHS', 'Y2K Cyber', 'Grunge Lo-Fi', 'Acid Glitch'],
    ARRAY['Indie Music Video', 'Fashion Lookbook', 'Album Teaser', 'Retro Commercial'],
    400.00, 2000.00, 'USD', 'available', 6, 'Prague, Czech Republic', 'https://retrovhs.demo.test',
    4.82, 31, false
),
(
    '00000000-0000-0000-0001-000000000011',
    '00000000-0000-0000-0000-000000000111',
    '@nordic_drone', 'Mia Lindqvist',
    'Acrobatic FPV Drone Pilot & Cinematic Aerialist',
    'Licensed commercial drone pilot diving mountains, drifting cars, and gliding through architectural spaces.',
    ARRAY['FPV Acrobatic Flight', '4K Aerial Cinematography', 'Horizon Leveling', 'Outdoor Tracking'],
    ARRAY['Custom 5-inch FPV Drone', 'DJI Inspire 3', 'GoPro Bones', 'Reelsteady GO'],
    ARRAY['Sweeping Nature', 'High-Speed Dynamic FPV', 'Nordic Crisp', 'Architectural Fly-Through'],
    ARRAY['Automotive Commercial', 'Real Estate Tour', 'Tourism Promo', 'Action Sports'],
    850.00, 3000.00, 'USD', 'available', 5, 'Stockholm, Sweden', 'https://nordicdrone.demo.test',
    4.94, 38, false
),
(
    '00000000-0000-0000-0001-000000000012',
    '00000000-0000-0000-0000-000000000112',
    '@tokyo_3d_vfx', 'Kenji Sato',
    'Unreal Engine 5 Virtual Production Director',
    'Building photorealistic virtual worlds, dynamic weather systems, and sci-fi digital commercials.',
    ARRAY['Unreal Engine 5', 'Virtual Production', 'Photogrammetry', 'Houdini FX Simulation'],
    ARRAY['Unreal Engine 5.4', 'Houdini', 'Substance Painter', 'DaVinci Resolve Studio'],
    ARRAY['Sci-Fi Cinematic', 'Photorealistic Virtual World', 'Dark Neon', 'Futuristic Industrial'],
    ARRAY['Virtual Commercial', 'Game Cinematic', 'Metaverse Promo', 'Sci-Fi Film Short'],
    2500.00, 10000.00, 'USD', 'unavailable', 11, 'Tokyo, Japan', 'https://tokyovfx.demo.test',
    5.00, 19, false
)
ON CONFLICT (id) DO UPDATE SET
    handle = EXCLUDED.handle,
    display_name = EXCLUDED.display_name,
    tagline = EXCLUDED.tagline,
    skills = EXCLUDED.skills,
    tools = EXCLUDED.tools,
    styles = EXCLUDED.styles,
    indicative_budget_min = EXCLUDED.indicative_budget_min,
    indicative_budget_max = EXCLUDED.indicative_budget_max,
    availability = EXCLUDED.availability;

-- ============================================================================
-- 3. PORTFOLIO ITEMS
-- ============================================================================

INSERT INTO public.portfolio_items (
    id, creator_id, title, description, video_url, thumbnail_url,
    content_type, style, aspect_ratio, duration_seconds, tools_used,
    is_featured, view_count, verification_status
)
VALUES
-- Elena Rostova (AI Video)
(
    '00000000-0000-0000-0002-000000000001',
    '00000000-0000-0000-0001-000000000001',
    'Neon Metropolis 2099 - AI Spec Ad',
    'Fully generated speculative luxury fragrance commercial combining Runway Gen-3 text-to-video with custom upscale.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
    'https://images.unsplash.com/photo-1508739773434-c26b3d09e071',
    'AI Concept', 'Cyberpunk', '16:9', 45,
    ARRAY['Runway Gen-3', 'Midjourney v6', 'Topaz Video AI'],
    true, 14200, 'verified'
),
(
    '00000000-0000-0000-0002-000000000002',
    '00000000-0000-0000-0001-000000000001',
    'Digital Flora: Morphing Botanical Organisms',
    'Surrealist looping micro-video generated for a contemporary fashion week digital backdrop.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
    'https://images.unsplash.com/photo-1518709268805-4e9042af9f23',
    'Fashion Promo', 'Sci-Fi Surrealism', '9:16', 20,
    ARRAY['ComfyUI', 'Topaz Video AI', 'DaVinci Resolve'],
    false, 8900, 'verified'
),

-- Marcus Vance (Editing & Pacing)
(
    '00000000-0000-0000-0002-000000000003',
    '00000000-0000-0000-0001-000000000002',
    'RedBull Speed Run: 60-Second Adrenaline Edit',
    'Multi-camera dynamic cut with sub-bass impacts, SFX layering, and seamless speed ramps.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    'https://images.unsplash.com/photo-1511512578047-dfb367046420',
    'Commercial', 'High-Energy', '16:9', 60,
    ARRAY['Adobe Premiere Pro', 'Logic Pro', 'After Effects'],
    true, 28100, 'verified'
),

-- Aoi Tanaka (3D Animation)
(
    '00000000-0000-0000-0002-000000000004',
    '00000000-0000-0000-0001-000000000003',
    'CloudPay: 3D Isometric FinTech Universe',
    'Whimsical 3D animation explaining automated cloud savings with pastel materials and clean lighting.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
    'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe',
    'Product 3D', '3D Stylized', '16:9', 75,
    ARRAY['Blender', 'Cinema 4D', 'Octane Render'],
    true, 19400, 'verified'
),

-- Liam O'Connor (Product Ads)
(
    '00000000-0000-0000-0002-000000000005',
    '00000000-0000-0000-0001-000000000004',
    'AURA Chronograph: Timepiece Macro Showcase',
    'Ultra-close macro shots of sapphire crystal, bevelled gear movement, and dramatic rim lighting.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
    'https://images.unsplash.com/photo-1523275335684-37898b6baf30',
    'Product Commercial', 'Luxury Clean', '16:9', 30,
    ARRAY['Sony FX6', 'DaVinci Resolve Studio', 'Cinema 4D'],
    true, 33500, 'verified'
),

-- Sofia Reyes (Cinematic)
(
    '00000000-0000-0000-0002-000000000006',
    '00000000-0000-0000-0001-000000000005',
    'Echoes of the Coast: 35mm Brand Odyssey',
    'Shot on location with vintage anamorphic lenses, natural golden hour illumination, and print film LUTs.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4',
    'https://images.unsplash.com/photo-1485846234645-a62644f84728',
    'Cinematic Short', '35mm Film Aesthetic', '21:9', 180,
    ARRAY['ARRI Alexa Mini LF', 'DaVinci Resolve Studio', 'Dehancer Pro'],
    true, 41200, 'verified'
),

-- Kavita Patel (Social Reels)
(
    '00000000-0000-0000-0002-000000000007',
    '00000000-0000-0000-0001-000000000006',
    '3 AI Hacks That Saved Me 20 Hours (Viral Reel)',
    'Fast 0.8s hook, kinetic pop-up text, dynamic zooms, and sound-synced cuts created for TikTok.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4',
    'https://images.unsplash.com/photo-1611162617474-5b21e879e113',
    'Social Reel', 'Snappy Viral', '9:16', 32,
    ARRAY['CapCut Desktop', 'Adobe Premiere Pro'],
    true, 92000, 'verified'
),

-- Julian Dubois (Event Recap)
(
    '00000000-0000-0000-0002-000000000008',
    '00000000-0000-0000-0001-000000000007',
    'Solaris Festival 2026: Official Aftermovie',
    'High-intensity low light concert footage with laser diffraction, pyro captures, and crowd energy.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
    'https://images.unsplash.com/photo-1470225620780-dba8ba36b745',
    'Event Recap', 'Euphoric Festival', '16:9', 120,
    ARRAY['Sony A7S III', 'DJI RS3 Pro', 'FilmConvert'],
    false, 21500, 'verified'
),

-- Chloe Martin (SaaS Explainer)
(
    '00000000-0000-0000-0002-000000000009',
    '00000000-0000-0000-0001-000000000009',
    'DevSync: Automated CI/CD Workflow Animation',
    'Vector UI mockup flows, smooth cursor physics, and micro-interactions illustrating developer tooling.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackSeeTheWorld.mp4',
    'https://images.unsplash.com/photo-1551288049-bebda4e38f71',
    'SaaS Explainer', 'Tech Clean', '16:9', 60,
    ARRAY['After Effects', 'Figma', 'Adobe Illustrator'],
    true, 16800, 'verified'
),

-- Dmitri Volkov (Retro VHS)
(
    '00000000-0000-0000-0002-000000000010',
    '00000000-0000-0000-0001-000000000010',
    'Neon Midnight: Synthesizer Tape Music Video',
    'Dubbed to physical VHS tape, re-recorded through a 1989 cathode-ray monitor with scan-line fringing.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
    'https://images.unsplash.com/photo-1550745165-9bc0b252726f',
    'Music Video', 'Retro VHS', '4:5', 150,
    ARRAY['Sony CRT Monitor', 'VHS Deck', 'TouchDesigner'],
    true, 18700, 'verified'
),

-- Mia Lindqvist (FPV Drone)
(
    '00000000-0000-0000-0002-000000000011',
    '00000000-0000-0000-0001-000000000011',
    'Fjord Diving: Acrobatic Aerial Chase',
    'Diving 800-meter sheer cliffs in Norway at 120km/h with gyroscopic stabilization and crisp cold tones.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4',
    'https://images.unsplash.com/photo-1508614589041-895b88991e3e',
    'Tourism Promo', 'High-Speed Dynamic FPV', '16:9', 48,
    ARRAY['Custom 5-inch FPV Drone', 'GoPro Bones', 'Reelsteady GO'],
    true, 39000, 'verified'
),

-- Kenji Sato (Unreal Engine 5)
(
    '00000000-0000-0000-0002-000000000012',
    '00000000-0000-0000-0001-000000000012',
    'Aethelgard: Real-Time Virtual Production Demo',
    'Cyberpunk rain-slicked boulevard generated in Unreal Engine 5 with real-time Lumen lighting and Nanite geometry.',
    'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WhatCarCanYouGetForAGrand.mp4',
    'https://images.unsplash.com/photo-1578632767115-351597cf2477',
    'Game Cinematic', 'Sci-Fi Cinematic', '21:9', 90,
    ARRAY['Unreal Engine 5.4', 'Houdini', 'Substance Painter'],
    true, 45000, 'verified'
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    video_url = EXCLUDED.video_url,
    content_type = EXCLUDED.content_type,
    style = EXCLUDED.style,
    tools_used = EXCLUDED.tools_used;

-- ============================================================================
-- 4. CUSTOMER BRIEFS
-- ============================================================================

INSERT INTO public.briefs (
    id, customer_id, title, description, ai_summary, target_audience,
    content_type, preferred_style, aspect_ratio, duration_seconds_target,
    budget_min, budget_max, currency, deadline, commercial_use_required,
    required_skills, preferred_tools, status
)
VALUES
(
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'Peak Endurance Shoe: High-Energy Launch Video',
    'We require a fast-paced, heart-pumping 45-second commercial showcasing our new trail running footwear in rugged terrains.',
    'AI Assistant Summary: 45s high-energy commercial for athletic trail shoe. Emphasize fast cuts, mud/water impacts, sound design, and product durability.',
    'Runners, outdoor athletes, and fitness enthusiasts aged 20-38',
    'Product Commercial', 'High-Energy', '16:9', 45,
    1500.00, 3500.00, 'USD', CURRENT_TIMESTAMP + INTERVAL '21 days', true,
    ARRAY['Fast Pacing Editing', 'Sound Design', 'Macro Product Cinematography'],
    ARRAY['Adobe Premiere Pro', 'Sony FX6', 'DaVinci Resolve'],
    'open'
),
(
    '00000000-0000-0000-0003-000000000002',
    '00000000-0000-0000-0000-000000000002',
    'Lumina AI Blood Diagnostics: 3D Animated Explainer',
    'Looking for a talented 3D animator to visualize how our microfluidic sensor detects biomarkers at the cellular level.',
    'AI Assistant Summary: 60s 3D medical explainer. Clean, trustworthy, stylized 3D microscopic visualization of cellular diagnostics.',
    'Hospital lab directors, doctors, and biotech investors',
    'Product 3D', '3D Stylized', '16:9', 60,
    2000.00, 4500.00, 'USD', CURRENT_TIMESTAMP + INTERVAL '30 days', true,
    ARRAY['3D Motion Graphics', 'Character Rigging', '3D Product CGI'],
    ARRAY['Blender', 'Cinema 4D', 'Octane Render'],
    'open'
),
(
    '00000000-0000-0000-0003-000000000003',
    '00000000-0000-0000-0000-000000000003',
    'Nova Card: 5x Viral TikTok / Reels Campaign',
    'Need a creator to script, edit, and deliver 5 native TikTok/Reels videos explaining cashback rewards for Gen-Z.',
    'AI Assistant Summary: Batch of 5 vertical short-form reels (15-30s each) with viral hooks, humor, and snappy on-screen typography.',
    'College students and early career professionals aged 18-26',
    'Social Reel', 'Snappy Viral', '9:16', 30,
    600.00, 1200.00, 'USD', CURRENT_TIMESTAMP + INTERVAL '14 days', true,
    ARRAY['Viral Hook Scripting', 'Kinetic Typography', 'Sound Trending Sync'],
    ARRAY['CapCut Desktop', 'Adobe Premiere Pro'],
    'in_review'
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    budget_min = EXCLUDED.budget_min,
    budget_max = EXCLUDED.budget_max,
    status = EXCLUDED.status;

-- ============================================================================
-- 5. ENQUIRIES
-- ============================================================================

INSERT INTO public.enquiries (
    id, customer_id, creator_id, brief_id, subject, message,
    proposed_budget, proposed_deadline, status
)
VALUES
(
    '00000000-0000-0000-0004-000000000001',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0001-000000000002',
    '00000000-0000-0000-0003-000000000001',
    'Inquiry about Peak Endurance Commercial Pacing',
    'Hi Marcus, loved your RedBull edit! We have raw 4K RED footage for our trail running campaign. Would you be available to handle the cut and sound mix within our $2,500 budget?',
    2500.00, CURRENT_TIMESTAMP + INTERVAL '18 days', 'accepted'
),
(
    '00000000-0000-0000-0004-000000000002',
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0001-000000000003',
    '00000000-0000-0000-0003-000000000002',
    '3D Medical Explainer for Lumina Diagnostics',
    'Hi Aoi, your 3D animation portfolio is gorgeous. Can you take a look at our brief for visualizing our diagnostic chip?',
    3500.00, CURRENT_TIMESTAMP + INTERVAL '28 days', 'pending'
)
ON CONFLICT (id) DO UPDATE SET
    subject = EXCLUDED.subject,
    message = EXCLUDED.message,
    status = EXCLUDED.status;

-- ============================================================================
-- 6. CREATOR INTERESTS (Pitches on Briefs)
-- ============================================================================

INSERT INTO public.creator_interests (
    id, brief_id, creator_id, pitch_note, estimated_delivery_days,
    proposed_quote, sample_portfolio_item_id, status
)
VALUES
(
    '00000000-0000-0000-0005-000000000001',
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0001-000000000002',
    'I have edited sports commercials for 6 years. I can deliver a rapid cut with customized sound design and impact transitions in 10 days.',
    10, 2400.00, '00000000-0000-0000-0002-000000000003', 'accepted'
),
(
    '00000000-0000-0000-0005-000000000002',
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0001-000000000004',
    'I can shoot macro slow-motion b-roll of your shoe sole and combine it with your footage for an elevated studio aesthetic.',
    14, 3200.00, '00000000-0000-0000-0002-000000000005', 'shortlisted'
),
(
    '00000000-0000-0000-0005-000000000003',
    '00000000-0000-0000-0003-000000000003',
    '00000000-0000-0000-0001-000000000006',
    'I specialize in FinTech short-form content. I can script and deliver all 5 reels with hooked captions within 7 days!',
    7, 950.00, '00000000-0000-0000-0002-000000000007', 'submitted'
)
ON CONFLICT (brief_id, creator_id) DO UPDATE SET
    pitch_note = EXCLUDED.pitch_note,
    proposed_quote = EXCLUDED.proposed_quote,
    status = EXCLUDED.status;

-- ============================================================================
-- 7. VERIFICATION SIGNALS (Trust & Evidence)
-- ============================================================================

INSERT INTO public.verification_signals (
    id, creator_id, portfolio_item_id, signal_type,
    evidence_url, metadata, status, verified_at, notes
)
VALUES
(
    '00000000-0000-0000-0006-000000000001',
    '00000000-0000-0000-0001-000000000001',
    '00000000-0000-0000-0002-000000000001',
    'tool_authenticity_confirmed',
    'https://demo-verification.test/runway-metadata/elena',
    '{"tool": "Runway Gen-3 Alpha", "generation_seed": 492019, "resolution": "4K Upscaled"}'::jsonb,
    'verified', CURRENT_TIMESTAMP - INTERVAL '3 days',
    'Demonstration verification: Runway generation prompt hashes verified.'
),
(
    '00000000-0000-0000-0006-000000000002',
    '00000000-0000-0000-0001-000000000002',
    '00000000-0000-0000-0002-000000000003',
    'portfolio_link_verified',
    'https://demo-verification.test/vimeo/marcus-vance',
    '{"platform": "Vimeo Pro", "embed_allowed": true, "original_client": "RedBull Media House"}'::jsonb,
    'verified', CURRENT_TIMESTAMP - INTERVAL '10 days',
    'Demonstration verification: Client accreditation on Vimeo confirmed.'
),
(
    '00000000-0000-0000-0006-000000000003',
    '00000000-0000-0000-0001-000000000004',
    '00000000-0000-0000-0002-000000000005',
    'identity_verified',
    'https://demo-verification.test/id/liam-oconnor',
    '{"id_type": "Passport", "country": "GB", "business_number": "UK-8291039"}'::jsonb,
    'verified', CURRENT_TIMESTAMP - INTERVAL '15 days',
    'Demonstration verification: Business registry verified.'
)
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status,
    notes = EXCLUDED.notes;

-- ============================================================================
-- 8. CREATOR PRIVATE CONTACT DETAILS (Isolated Behind Contact Unlock)
-- ============================================================================

INSERT INTO public.creator_private_contacts (
    creator_id, legal_name, contact_email, phone_number, billing_address
)
VALUES
('00000000-0000-0000-0001-000000000001', 'Elena Rostova Studio LLC', 'direct.elena@rostovafilms.test', '+1-555-019-2831', '404 Innovation Way, San Francisco, CA 94107'),
('00000000-0000-0000-0001-000000000002', 'Marcus Vance Post-Production', 'contact@vanceedits.test', '+1-555-014-9922', '120 Sunset Blvd, Los Angeles, CA 90028'),
('00000000-0000-0000-0001-000000000003', 'Aoi Tanaka Motion Design', 'aoi@tanakadesign.test', '+81-3-5555-0143', 'Shibuya 2-Chome, Tokyo, Japan'),
('00000000-0000-0000-0001-000000000004', 'Liam O''Connor Visuals Ltd', 'liam@oconnorcine.test', '+44-20-7946-0912', 'Soho Square, London W1D 3QL, UK'),
('00000000-0000-0000-0001-000000000005', 'Sofia Reyes Cinema', 'sofia@reyesnarrative.test', '+34-91-123-4567', 'Gran Via 42, Madrid, Spain'),
('00000000-0000-0000-0001-000000000006', 'Kavita Patel Media', 'kavita@viralsocial.test', '+91-22-2654-9870', 'Bandra West, Mumbai 400050, India'),
('00000000-0000-0000-0001-000000000007', 'Julian Dubois Productions', 'julian@duboisrecap.test', '+33-1-42-68-55-00', 'Rue de Rivoli, Paris 75001, France'),
('00000000-0000-0000-0001-000000000008', 'Tariq Al-Mansoor NeRF Studio', 'tariq@neuralvfx.test', '+971-4-368-0000', 'Dubai Media City, Dubai, UAE'),
('00000000-0000-0000-0001-000000000009', 'Chloe Martin Motion Lab', 'chloe@saasmotion.test', '+1-416-555-0182', 'King St West, Toronto, ON M5V 1J5, Canada'),
('00000000-0000-0000-0001-000000000010', 'Dmitri Volkov Analog Lab', 'dmitri@retrovhs.test', '+49-30-2312-5555', 'Kreuzberg, Berlin 10999, Germany'),
('00000000-0000-0000-0001-000000000011', 'Mia Lindqvist Aerials', 'mia@nordicfpv.test', '+46-8-123-4567', 'Sodermalm, Stockholm 11820, Sweden'),
('00000000-0000-0000-0001-000000000012', 'Kenji Sato Unreal Worlds', 'kenji@satovirtual.test', '+81-6-6555-0199', 'Umeda, Osaka, Japan')
ON CONFLICT (creator_id) DO UPDATE SET
    legal_name = EXCLUDED.legal_name,
    contact_email = EXCLUDED.contact_email,
    phone_number = EXCLUDED.phone_number;

-- ============================================================================
-- 9. AI BRIEF CONVERSATION & REVISION HISTORY
-- ============================================================================

INSERT INTO public.brief_ai_sessions (
    id, customer_id, brief_id, session_title, status
)
VALUES (
    '00000000-0000-0000-0007-000000000001',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0003-000000000001',
    'Hyper-Energy Footwear Commercial Brief Assistant',
    'completed'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.brief_ai_messages (
    id, session_id, sender_role, content, clarification_field, model_metadata
)
VALUES
(
    '00000000-0000-0000-0008-000000000001',
    '00000000-0000-0000-0007-000000000001',
    'customer',
    'We need a 30-second commercial for our new trail running sneaker. Needs to feel fast and cinematic.',
    NULL,
    '{}'::jsonb
),
(
    '00000000-0000-0000-0008-000000000002',
    '00000000-0000-0000-0007-000000000001',
    'assistant',
    'That sounds exciting! What aspect ratio and target platforms are you prioritizing (e.g. 16:9 widescreen or 9:16 vertical)? And do you have a target delivery deadline?',
    'aspect_ratio_and_deadline',
    '{"model": "gemini-1.5-pro", "temperature": 0.3}'::jsonb
),
(
    '00000000-0000-0000-0008-000000000003',
    '00000000-0000-0000-0007-000000000001',
    'customer',
    'Both 16:9 for YouTube and 9:16 cuts for Reels. Need delivery within 3 weeks before our launch date.',
    'deliverables',
    '{}'::jsonb
),
(
    '00000000-0000-0000-0008-000000000004',
    '00000000-0000-0000-0007-000000000001',
    'assistant',
    'I have compiled your requirements into a structured brief with budget $2,500 - $4,500 and 2 revision rounds. Please review and approve below.',
    'approval_ready',
    '{"model": "gemini-1.5-pro"}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.brief_revisions (
    id, brief_id, revision_number, snapshot_data, changed_by, change_summary
)
VALUES (
    '00000000-0000-0000-0009-000000000001',
    '00000000-0000-0000-0003-000000000001',
    1,
    '{"title": "High-Energy Trail Running Sneaker Commercial", "duration_seconds": 30, "aspect_ratio": "16:9", "budget_max": 4500}'::jsonb,
    '00000000-0000-0000-0000-000000000001',
    'Initial AI generated brief approved by Alice Walker.'
)
ON CONFLICT (brief_id, revision_number) DO NOTHING;

-- ============================================================================
-- 10. CREATOR MATCHING SNAPSHOTS
-- ============================================================================

INSERT INTO public.brief_matches (
    id, brief_id, creator_id, match_score, match_reasons, is_notified
)
VALUES
(
    '00000000-0000-0000-0010-000000000001',
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0001-000000000001',
    96.50,
    '["98% match on Runway Gen-3 AI generation", "Within indicative budget range", "High 4.95 customer rating"]'::jsonb,
    true
),
(
    '00000000-0000-0000-0010-000000000002',
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0001-000000000002',
    91.00,
    '["100% match on fast pacing editing", "Commercial portfolio in athletic apparel"]'::jsonb,
    true
)
ON CONFLICT (brief_id, creator_id) DO UPDATE SET
    match_score = EXCLUDED.match_score;

-- ============================================================================
-- 11. IN-PLATFORM CHAT & CONTACT CENSORSHIP DEMO
-- ============================================================================

INSERT INTO public.chat_conversations (
    id, project_id, brief_id, created_by, status
)
VALUES (
    '00000000-0000-0000-0011-000000000001',
    NULL,
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'active'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.chat_participants (
    id, conversation_id, user_id, role, display_alias
)
VALUES
(
    '00000000-0000-0000-0012-000000000001',
    '00000000-0000-0000-0011-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'customer',
    'Alice Walker (Peak Athletics)'
),
(
    '00000000-0000-0000-0012-000000000002',
    '00000000-0000-0000-0011-000000000001',
    '00000000-0000-0000-0000-000000000101',
    'creator',
    'Creator #A001 (AI Video Specialist)'
)
ON CONFLICT (conversation_id, user_id) DO UPDATE SET
    display_alias = EXCLUDED.display_alias;

INSERT INTO public.chat_messages (
    id, conversation_id, sender_id, content, moderation_status
)
VALUES
(
    '00000000-0000-0000-0013-000000000001',
    '00000000-0000-0000-0011-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'Hello! Loved your AI motion portfolio samples. Could you deliver 3 concept drafts in 7 days?',
    'allowed'
),
(
    '00000000-0000-0000-0013-000000000002',
    '00000000-0000-0000-0011-000000000001',
    '00000000-0000-0000-0000-000000000101',
    'Hi Alice! Yes, I can generate 3 distinct neural camera passes with sound design in 6 days.',
    'allowed'
),
(
    '00000000-0000-0000-0013-000000000003',
    '00000000-0000-0000-0011-000000000001',
    '00000000-0000-0000-0000-000000000101',
    'If you prefer to chat directly off-platform, my WhatsApp is +1-555-019-2831.',
    'blocked'
)
ON CONFLICT (id) DO NOTHING;

-- Message moderation audit record for the blocked message
INSERT INTO public.message_moderation_logs (
    id, message_id, flagged_by, detection_category, redacted_snippet, moderation_decision
)
VALUES (
    '00000000-0000-0000-0014-000000000001',
    '00000000-0000-0000-0013-000000000003',
    'system_regex',
    'phone_number',
    '+1-555-019-2831',
    'blocked'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 12. PROJECT QUOTES (Private Creator Quote vs Customer Price)
-- ============================================================================

INSERT INTO public.project_quotes (
    id, brief_id, creator_id,
    creator_quote_amount, platform_fee_rate, platform_fee_amount, tax_amount, customer_price_amount,
    currency, scope_summary, deliverables, estimated_delivery_days, revision_count, valid_until, status
)
VALUES (
    '00000000-0000-0000-0015-000000000001',
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0001-000000000001',
    2500.00, 0.1500, 375.00, 0.00, 2875.00,
    'USD',
    '30s 4K AI hybrid trailer + 9:16 vertical cuts with full commercial license.',
    ARRAY['1x 4K Master Video (16:9)', '2x Social Cutdowns (9:16)', 'Full Commercial Usage Rights'],
    7, 2, CURRENT_TIMESTAMP + INTERVAL '14 days',
    'presented_to_customer'
)
ON CONFLICT (brief_id, creator_id) DO UPDATE SET
    status = EXCLUDED.status,
    customer_price_amount = EXCLUDED.customer_price_amount;

-- ============================================================================
-- 13. FORMAL CONTRACT PROJECTS & COMPLETED DEALS
-- ============================================================================

-- Project 1: Lumina Health 3D Animation (COMPLETED)
INSERT INTO public.projects (
    id, brief_id, quote_id, customer_id, creator_id,
    title, agreed_amount, creator_earnings, platform_fee, currency,
    status, started_at, completed_at
)
VALUES (
    '00000000-0000-0000-0016-000000000001',
    '00000000-0000-0000-0003-000000000002',
    NULL,
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0001-000000000003',
    '3D Medical Animation for Lumina Health Nanobot Delivery',
    6000.00, 5100.00, 900.00, 'USD',
    'completed',
    CURRENT_TIMESTAMP - INTERVAL '30 days',
    CURRENT_TIMESTAMP - INTERVAL '5 days'
)
ON CONFLICT (id) DO NOTHING;

-- Project 2: Peak Athletics (IN PROGRESS)
INSERT INTO public.projects (
    id, brief_id, quote_id, customer_id, creator_id,
    title, agreed_amount, creator_earnings, platform_fee, currency,
    status, started_at
)
VALUES (
    '00000000-0000-0000-0016-000000000002',
    '00000000-0000-0000-0003-000000000001',
    '00000000-0000-0000-0015-000000000001',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0001-000000000001',
    'Peak Athletics High-Energy Footwear Commercial',
    2875.00, 2500.00, 375.00, 'USD',
    'in_progress',
    CURRENT_TIMESTAMP - INTERVAL '2 days'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- 14. PAYMENTS, FINANCIAL LEDGER & VERIFIED CONTACT UNLOCKS
-- ============================================================================

INSERT INTO public.payments (
    id, project_id, quote_id, customer_id, provider, provider_payment_intent_id,
    amount, currency, status, idempotency_key
)
VALUES
(
    '00000000-0000-0000-0017-000000000001',
    '00000000-0000-0000-0016-000000000001',
    NULL,
    '00000000-0000-0000-0000-000000000002',
    'stripe',
    'pi_demo_lumina_001',
    6000.00, 'USD', 'succeeded',
    'idem_lumina_health_001'
),
(
    '00000000-0000-0000-0017-000000000002',
    '00000000-0000-0000-0016-000000000002',
    '00000000-0000-0000-0015-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'stripe',
    'pi_demo_peak_002',
    2875.00, 'USD', 'succeeded',
    'idem_peak_athletics_002'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.financial_ledger (
    id, payment_id, entry_type, account, amount, currency, reference_id
)
VALUES
(
    '00000000-0000-0000-0018-000000000001',
    '00000000-0000-0000-0017-000000000001',
    'payment_received', 'escrow_holding', 6000.00, 'USD', 'stripe_ch_001'
),
(
    '00000000-0000-0000-0018-000000000002',
    '00000000-0000-0000-0017-000000000001',
    'platform_fee', 'platform_revenue', 900.00, 'USD', 'fee_lumina_001'
),
(
    '00000000-0000-0000-0018-000000000003',
    '00000000-0000-0000-0017-000000000001',
    'creator_payout', 'creator_payable', 5100.00, 'USD', 'payout_aoi_001'
)
ON CONFLICT (id) DO NOTHING;

-- Verified contact unlock for Alice Walker after confirmed escrow payment
INSERT INTO public.contact_unlocks (
    id, customer_id, creator_id, project_id, payment_id, status
)
VALUES (
    '00000000-0000-0000-0019-000000000001',
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0001-000000000001',
    '00000000-0000-0000-0016-000000000002',
    '00000000-0000-0000-0017-000000000002',
    'active'
)
ON CONFLICT (customer_id, creator_id) DO UPDATE SET
    status = EXCLUDED.status;

-- ============================================================================
-- 15. VERIFIED REVIEWS & CREATOR SUBSCRIPTIONS
-- ============================================================================

-- Review submitted by David Chen for Aoi Tanaka on completed 3D animation
INSERT INTO public.reviews (
    id, project_id, customer_id, creator_id, rating, review_text, moderation_status
)
VALUES (
    '00000000-0000-0000-0020-000000000001',
    '00000000-0000-0000-0016-000000000001',
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0001-000000000003',
    5.00,
    'Exceptional 3D medical animation! Aoi understood our complex nanobot brief immediately and delivered ahead of schedule.',
    'published'
)
ON CONFLICT (project_id) DO NOTHING;

-- Creator Subscriptions (Elena on Pro, Marcus on Starter, others on Free)
INSERT INTO public.creator_subscriptions (
    id, creator_id, tier, status, billing_cycle
)
VALUES
(
    '00000000-0000-0000-0021-000000000001',
    '00000000-0000-0000-0001-000000000001',
    'pro', 'active', 'monthly'
),
(
    '00000000-0000-0000-0021-000000000002',
    '00000000-0000-0000-0001-000000000002',
    'starter', 'active', 'monthly'
)
ON CONFLICT (id) DO NOTHING;

