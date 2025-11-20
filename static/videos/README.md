# Video Files Directory

This directory is for storing course video files.

## How to Add Videos:

### Option 1: Upload via Django Admin
1. Go to `http://localhost:8000/admin/`
2. Navigate to **Courses** → **Sessions**
3. Edit your session
4. Upload a video file in the **Video File** field

### Option 2: Add Video Files Manually
1. Place your `.mp4` video files in this directory
2. Update the session's **Video URL** to point to your file
3. Example: `/static/videos/your-video.mp4`

### Supported Formats:
- MP4 (recommended)
- WebM
- OGG

### File Size:
- Keep videos under 100MB for best performance
- Consider compressing large files

## Current Test Video:
- `sample-course.mp4` - Placeholder video (you can replace this)


