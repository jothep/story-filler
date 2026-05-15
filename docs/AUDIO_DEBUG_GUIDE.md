# Audio Debugging Guide - M4A Playback Issue

**Date**: 2026-05-01  
**Issue**: M4A audio files not playing on iPad, but MP3 BGM works fine

---

## Test with Console

### Step 1: Open Safari Developer Tools on iPad

1. Connect iPad to Mac via USB/WiFi
2. Mac Safari → Develop → [Your iPad Name] → [Page Tab]
3. Open Console

### Step 2: Check Audio File Details

When you click "Reading" button, console will log:
```
Attempting to play audio: <URL>
```

**Check**:
- Is the URL correct?
- Does it end with `.m4a`?
- Is it from correct domain?

### Step 3: Check for Errors

Look for errors in console:
- **Error code 4**: Format not supported (M4A codec issue)
- **Error code 2**: Network error (CORS or 404)
- **Error code 3**: Decoding error (corrupted file)

---

## Known M4A Issues on iOS

### Issue 1: M4A Codec Variants

M4A is a container format. Safari supports:
- ✅ AAC-LC codec (most common)
- ✅ HE-AAC (efficient)
- ❌ ALAC (lossless) - limited support
- ❌ Some proprietary codecs

**Check your M4A files**:
```bash
# On Mac with ffmpeg
ffmpeg -i your_audio.m4a

# Look for:
# Audio: aac (mp4a / 0x6134706D) <- Good
# Audio: alac <- May not work
```

### Issue 2: CORS Headers

M4A files served from Cloud Storage need CORS headers.

**Check in browser console**:
```javascript
fetch('https://storage.googleapis.com/.../audio.m4a', { method: 'HEAD' })
  .then(r => console.log(r.headers.get('access-control-allow-origin')))
```

Should return: `*` or your domain

---

## Solution 1: Convert M4A to MP3

Most reliable for iOS compatibility:

```bash
# Install ffmpeg (if not installed)
brew install ffmpeg

# Convert M4A to MP3
ffmpeg -i input.m4a -codec:a libmp3lame -qscale:a 2 output.mp3

# Or convert entire directory
for file in *.m4a; do
  ffmpeg -i "$file" -codec:a libmp3lame -qscale:a 2 "${file%.m4a}.mp3"
done
```

**Why MP3?**
- ✅ Universal browser support (iOS, Android, all browsers)
- ✅ Smaller file size than uncompressed M4A
- ✅ No codec compatibility issues

---

## Solution 2: Use HTML5 Audio Element

Instead of `new Audio()`, use an actual `<audio>` element:

```javascript
// Current (problematic)
const audio = new Audio(audioUrl);
audio.play();

// Better (more iOS-compatible)
const audioElement = document.createElement('audio');
audioElement.src = audioUrl;
audioElement.type = 'audio/mp4'; // Explicit MIME type
document.body.appendChild(audioElement); // Must be in DOM
audioElement.play();
```

---

## Solution 3: Add Multiple Sources

Fallback to MP3 if M4A fails:

```jsx
<audio controls>
  <source src="audio.m4a" type="audio/mp4" />
  <source src="audio.mp3" type="audio/mpeg" />
  Your browser doesn't support audio.
</audio>
```

---

## Temporary Workaround

**For testing**, manually convert files to MP3 and re-upload.

**Long-term**, add automatic conversion in backend:

```python
# In Django model save()
from pydub import AudioSegment

def save(self, *args, **kwargs):
    if self.audio_file and self.audio_file.name.endswith('.m4a'):
        # Convert to MP3
        audio = AudioSegment.from_file(self.audio_file, format='m4a')
        mp3_buffer = BytesIO()
        audio.export(mp3_buffer, format='mp3', bitrate='128k')
        
        # Replace with MP3
        filename = self.audio_file.name.replace('.m4a', '.mp3')
        self.audio_file.save(filename, File(mp3_buffer), save=False)
    
    super().save(*args, **kwargs)
```

---

## Recommended Action

1. **Check console logs** to confirm M4A is the issue
2. **Convert one M4A file to MP3** for testing
3. If MP3 works, **batch convert all files**
4. Update backend to accept both formats

---

## Browser Compatibility

| Format | Chrome | Safari | Firefox | iOS Safari |
|--------|--------|--------|---------|------------|
| MP3 | ✅ | ✅ | ✅ | ✅ |
| M4A (AAC) | ✅ | ✅ | ❌ | ⚠️ (depends on codec) |
| OGG | ✅ | ❌ | ✅ | ❌ |
| WAV | ✅ | ✅ | ✅ | ✅ (large files) |

**Winner**: MP3 (universal support)

---

**Next Steps**: Deploy improved error logging, test on iPad, check console output.
