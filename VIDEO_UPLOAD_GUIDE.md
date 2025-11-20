# Video Upload Guide

## How to Upload Videos Through Django Admin

### Step 1: Access Django Admin
1. Go to: `http://localhost:8000/admin/`
2. Login with your admin credentials

### Step 2: Navigate to Sessions
1. Click on **"Courses"** in the main menu
2. Click on **"Sessions"** in the Courses section
3. Find your session **"[poiuy"** (ID: 69)
4. Click on it to edit

### Step 3: Upload Your Video
1. Scroll down to find the **"Video File"** field
2. Click **"Choose File"** or **"Browse"**
3. Select your video file from your computer
4. **Supported formats**: MP4, WebM, OGG, MOV
5. **Recommended**: MP4 format for best compatibility

### Step 4: Save
1. Click **"Save"** at the bottom of the page
2. Your video will be uploaded and processed

### Step 5: Test Your Course
1. Go to: `http://localhost:8000/course/9/`
2. Your video should now play in the course player

## Video Requirements

### File Size
- **Recommended**: Under 100MB for best performance
- **Maximum**: 500MB (depending on server settings)

### Formats
- **MP4** (recommended) - Best browser support
- **WebM** - Good for modern browsers
- **OGG** - Alternative format
- **MOV** - Apple format (may need conversion)

### Resolution
- **Recommended**: 720p (1280x720) or 1080p (1920x1080)
- **Aspect Ratio**: 16:9 for best display

## Troubleshooting

### If Video Doesn't Play
1. Check the debug info on the course page
2. Make sure the file format is supported
3. Try a different browser
4. Check file size (too large files may not load)

### If Upload Fails
1. Check file size (try smaller file)
2. Check file format (convert to MP4)
3. Check server storage space
4. Try uploading in smaller chunks

## Alternative: Video URL
If you prefer to use video links instead of uploading files:
1. In the session edit page, use the **"Video URL"** field
2. Paste a direct link to your video file
3. Make sure the URL points directly to a video file (not a webpage)

## Need Help?
- Check the debug info on the course page
- Make sure Django server is running
- Check browser console for errors


