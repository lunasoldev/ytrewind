from bs4 import BeautifulSoup
import json
import re

def clean_title(title, url, full_text):
    """Clean and validate the video title"""
    if not title or title == url:  # If title is empty or same as URL
        # Try to extract title from "angesehen" pattern
        title_match = re.search(r'(.*?)\s+angesehen', full_text)
        if title_match:
            return title_match.group(1).strip()
        return "Unknown Title"
    return title.strip()

def extract_channel_info(entry):
    """Extract channel name and URL"""
    channel_tags = entry.find_all('a', href=True)
    
    # Skip the first link (video link) and look for channel link
    for tag in channel_tags[1:]:
        href = tag['href']
        if '/channel/' in href or '/user/' in href or '/c/' in href:
            return tag.text.strip(), href
    
    return 'Unknown', 'N/A'

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
total_entries = len(content_cells)
videos = []
count = 0

for entry in content_cells:
    try:
        print(f'Processing entry {count + 1}/{total_entries}...', flush=True)
        
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
        
        # Only append if we have at least a valid URL or title
        if video_url != 'N/A' or video_title != 'Unknown Title':
            videos.append({
                'title': video_title,
                'url': video_url,
                'channel': channel_name,
                'channelurl': channel_url,
                'timestamp': timestamp
            })
            
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} entries...", flush=True)
            
    except Exception as e:
        print(f"Error processing entry {count + 1}: {e}", flush=True)
        continue

# Save results
try:
    with open('watch_history.json', 'w', encoding='utf-8') as json_file:
        json.dump(videos, json_file, ensure_ascii=False, indent=4)
    print(f'Successfully saved {len(videos)} entries to watch_history.json', flush=True)
except Exception as e:
    print(f"Error saving JSON file: {e}", flush=True)
