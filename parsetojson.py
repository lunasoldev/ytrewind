from bs4 import BeautifulSoup
import json
import re

def clean_title(title, url, full_text):
    """Clean and validate the video title"""
    if not title:
        return "Unknown Title"
    
    title = title.strip()
    
    # If title is just a URL, try to find a better title
    if title.startswith('http'):
        # Try to extract title from "angesehen" pattern
        title_match = re.search(r'(.*?)\s+angesehen', full_text)
        if title_match:
            potential_title = title_match.group(1).strip()
            # Only use if it's not a URL
            if not potential_title.startswith('http'):
                return potential_title
        return "Unknown Title"
    
    return title

def extract_channel_info(entry):
    """Extract channel name and URL"""
    channel_tags = entry.find_all('a', href=True)
    
    # Skip the first link (video link) and look for channel link
    for tag in channel_tags[1:]:
        href = tag['href']
        # Check if it's a channel URL
        if any(x in href for x in ['/channel/', '/user/', '/c/']):
            return tag.text.strip(), href
    
    return 'Unknown', 'N/A'

def is_valid_youtube_entry(entry):
    """Check if the entry is a valid YouTube video entry"""
    # Check for video URL
    links = entry.find_all('a', href=True)
    if not links:
        return False
    
    first_link = links[0]['href']
    # Verify it's a YouTube video link
    if not ('youtube.com/watch?' in first_link or 'youtu.be/' in first_link):
        return False
        
    # Check for timestamp format
    text = entry.get_text()
    if not re.search(r'\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}:\d{2}\s+MEZ', text):
        return False
        
    return True

def parse_timestamp(text):
    """Extract and validate timestamp"""
    timestamp_pattern = r'(\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}:\d{2}\s+MEZ)'
    match = re.search(timestamp_pattern, text)
    return match.group(1) if match else 'N/A'

print('Opening file...', flush=True)

try:
    with open('Wiedergabeverlauf.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
except Exception as e:
    print(f"Error reading file: {e}", flush=True)
    exit(1)

print('File opened...', flush=True)

soup = BeautifulSoup(html_content, 'lxml')
content_cells = soup.find_all('div', class_='content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1')
videos = []
count = 0
skipped = 0

for entry in content_cells:
    try:
        # First check if this is a valid YouTube video entry
        if not is_valid_youtube_entry(entry):
            skipped += 1
            continue
            
        # Get full text content for backup parsing
        full_text = entry.get_text(separator=" ", strip=True)
        
        # Extract video information
        video_link = entry.find('a')
        video_url = video_link['href'] if video_link and 'href' in video_link.attrs else 'N/A'
        
        # Get and clean title
        video_title = video_link.text if video_link else ''
        video_title = clean_title(video_title, video_url, full_text)
        
        # Get channel information
        channel_name, channel_url = extract_channel_info(entry)
        
        # Get timestamp
        timestamp = parse_timestamp(full_text)
        
        # Only append if we have valid data
        if video_url != 'N/A' and video_title != 'Unknown Title':
            videos.append({
                'title': video_title,
                'url': video_url,
                'channel': channel_name,
                'channelurl': channel_url,
                'timestamp': timestamp
            })
            
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} entries (skipped {skipped})...", flush=True)
            
    except Exception as e:
        print(f"Error processing entry {count + 1}: {e}", flush=True)
        continue

# Save results
try:
    with open('watch_history.json', 'w', encoding='utf-8') as json_file:
        json.dump(videos, json_file, ensure_ascii=False, indent=4)
    print(f'Successfully saved {len(videos)} entries to watch_history.json', flush=True)
    print(f'Skipped {skipped} invalid entries', flush=True)
except Exception as e:
    print(f"Error saving JSON file: {e}", flush=True)
