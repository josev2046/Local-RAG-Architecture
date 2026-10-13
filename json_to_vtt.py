import os
import json

TRANSCRIPTS_DIR = "transcripts"

def format_timestamp(seconds):
    """Converts raw seconds into WebVTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def convert_json_to_vtt():
    if not os.path.exists(TRANSCRIPTS_DIR):
        print(f"Error: Directory '{TRANSCRIPTS_DIR}' not found.")
        return

    json_files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.json')]

    if not json_files:
        print(f"No JSON transcript files found in ./{TRANSCRIPTS_DIR}/")
        return

    print(f"Converting {len(json_files)} JSON transcripts to WebVTT captions...")

    converted_count = 0
    for filename in json_files:
        json_path = os.path.join(TRANSCRIPTS_DIR, filename)
        vtt_filename = filename.replace('.json', '.vtt')
        vtt_path = os.path.join(TRANSCRIPTS_DIR, vtt_filename)

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            segments = data.get('segments', [])

            with open(vtt_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for seg in segments:
                    start = format_timestamp(seg['start'])
                    end = format_timestamp(seg['end'])
                    text = seg['text'].strip()
                    f.write(f"{start} --> {end}\n{text}\n\n")

            converted_count += 1
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")

    print(f"Done! Successfully generated {converted_count} .vtt caption files in ./{TRANSCRIPTS_DIR}/")

if __name__ == "__main__":
    convert_json_to_vtt()
