import json
from server.db.session import SessionLocal
from server.db.models import Profile, CreatorProfile, PortfolioItem

def seed_qa_creators():
    db = SessionLocal()
    creators_data = [
        {
            "id": "creator_studio_phantom",
            "username": "studio_phantom",
            "display_name": "Studio Phantom",
            "avatar_url": "/assets/v1_06.jpg",
            "bio": "Hyper-realistic FLUX.1 commercials & cinematic sneakers",
            "specializations": ["Hyper-realistic FLUX.1 commercials & cinematic sneakers"],
            "ai_tools": ["FLUX.1", "ComfyUI", "Runway Gen-3"],
            "skills": ["Camera Motion Control", "LoRA Fine-Tuning", "Kinetic Lighting"],
            "hourly_compute_rate": 45.0,
            "base_model": "FLUX.1 Dev + ComfyUI"
        },
        {
            "id": "creator_cipher_canvas",
            "username": "cipher_canvas",
            "display_name": "Cipher Canvas",
            "avatar_url": "/assets/v2_02.jpg",
            "bio": "High-fashion editorial lookbooks & photoreal luxury apparel",
            "specializations": ["High-fashion editorial lookbooks & photoreal luxury apparel"],
            "ai_tools": ["FLUX.1", "ComfyUI", "Runway Gen-3"],
            "skills": ["Editorial Lighting", "Texture Consistency", "Style Transfer"],
            "hourly_compute_rate": 60.0,
            "base_model": "Midjourney v6 + Magnific AI"
        }
    ]

    for cd in creators_data:
        p = db.query(Profile).filter(Profile.id == cd["id"]).first()
        if not p:
            p = Profile(
                id=cd["id"],
                username=cd["username"],
                normalized_username=cd["username"].lower(),
                password_hash="hashed_pw_demo",
                display_name=cd["display_name"],
                avatar_url=cd["avatar_url"],
                bio=cd["bio"],
                role="creator",
                account_status="active",
                anonymous_mode=True,
                masked_alias=cd["display_name"]
            )
            db.add(p)
            db.flush()
        else:
            p.display_name = cd["display_name"]
            p.avatar_url = cd["avatar_url"]
            p.masked_alias = cd["display_name"]
            p.role = "creator"
            p.account_status = "active"

        cp = db.query(CreatorProfile).filter(CreatorProfile.user_id == cd["id"]).first()
        if not cp:
            cp = CreatorProfile(
                user_id=cd["id"],
                specializations=json.dumps(cd["specializations"]),
                skills=json.dumps(cd["skills"]),
                ai_tools=json.dumps(cd["ai_tools"]),
                ai_models=json.dumps(cd["ai_tools"]),
                hourly_compute_rate=cd["hourly_compute_rate"],
                base_model=cd["base_model"],
                availability_status="available",
                accepting_projects=True,
                profile_visibility="public"
            )
            db.add(cp)
        else:
            cp.ai_tools = json.dumps(cd["ai_tools"])
            cp.hourly_compute_rate = cd["hourly_compute_rate"]
            cp.specializations = json.dumps(cd["specializations"])

    db.commit()
    db.close()
    print("Successfully seeded Studio Phantom and Cipher Canvas in database.")

if __name__ == "__main__":
    seed_qa_creators()
