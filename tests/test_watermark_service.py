"""
Unit and Integration Tests for Dynamic Server-Side Watermark Service.
Tests image and video watermarking, token generation, and draft submission pipeline.
"""

import os
import tempfile
import pytest
from PIL import Image
import cv2

from server.services.watermark_service import WatermarkService
from server.db.session import SessionLocal, Base, engine


@pytest.fixture(scope="module")
def sample_image():
    """Generates a temporary sample test image."""
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img = Image.new("RGB", (640, 480), color=(50, 80, 120))
    img.save(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="module")
def sample_video():
    """Generates a temporary sample test video."""
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    width, height = 320, 240
    fps = 15.0
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    import numpy as np
    for _ in range(15):
        frame = np.full((height, width, 3), (40, 60, 90), dtype=np.uint8)
        out.write(frame)
    out.release()
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_watermark_token_generation():
    token = WatermarkService.generate_watermark_token("proj_123", "creator_abc")
    assert token.startswith("CG-DRAFT-")
    assert len(token) > 15


def test_burn_image_watermark(sample_image):
    fd, out_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    try:
        res = WatermarkService.burn_image_watermark(
            input_path=sample_image,
            output_path=out_path,
            project_id="proj_test_img",
            client_id="brand_client_1"
        )
        assert res["status"] == "watermarked"
        assert res["media_type"] == "image"
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
        assert "sha256" in res
        assert "watermark_token" in res
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)


def test_burn_video_watermark(sample_video):
    fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    try:
        res = WatermarkService.burn_video_watermark(
            input_path=sample_video,
            output_path=out_path,
            project_id="proj_test_vid",
            client_id="brand_client_2",
            max_frames=10
        )
        assert res["status"] == "watermarked"
        assert res["media_type"] == "video"
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
        assert res["frames_processed"] > 0
        assert "sha256" in res
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)


def test_process_draft_submission_image(sample_image):
    db = SessionLocal()
    try:
        draft = WatermarkService.process_draft_submission(
            db=db,
            project_id="proj_mock_01",
            creator_id="creator_mock_01",
            file_path=sample_image,
            title="Rough Cut Keyframe 1"
        )
        assert draft["file_type"] == "image"
        assert "watermarked_file_path" in draft
        assert os.path.exists(draft["watermarked_file_path"])
        assert draft["status"] == "under_review"
        assert draft["watermark_token"].startswith("CG-DRAFT-")
    finally:
        db.close()
