import time
import re
import requests
import sys
import html

from config import *
from cs_helpers import send_public_message

# Keep track of vessel identifiers we have already posted to avoid duplicates
posted_vessels = set()

def get_messages(room_name):
    """
    Fetches messages for the specified room using the ChatSurfer API.
    """
    domain_id = "chatsurferxmppunclass"
    url = f"https://{CS_HOST}/api/chat/messages/{domain_id}/{room_name}"
    params = {"api-key": CHATKEY}
    
    try:
        response = requests.get(
            url,
            params=params,
            cert=(CERT_PATH, KEY_PATH),
            verify=CA_BUNDLE_PATH,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Error] Failed to fetch messages for {room_name}: {response.status_code} {response.text}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"[Error] Exception fetching messages for {room_name}: {e}", file=sys.stderr)
        return None

def get_most_recent_message(room_name):
    """
    Fetches the single most recent message from the room.
    """
    data = get_messages(room_name)
    if not data or "messages" not in data or not data["messages"]:
        return None
    # Sort messages by timestamp to find the latest
    messages = data["messages"]
    return max(messages, key=lambda m: m.get("timestamp", ""))

def extract_vessel_identifiers(text):
    """
    Extracts vessel identifiers enclosed in angle brackets, e.g. <vessel_name vessel_number>.
    Normalizes spaces inside the brackets to ensure consistent matching.
    """
    if not text:
        return set()
    # Decode HTML entities (e.g. &lt; -> <)
    unescaped = html.unescape(text)
    matches = re.findall(r'<([^>]+)>', unescaped)
    normalized = set()
    for m in matches:
        # Normalize whitespace
        clean = " ".join(m.split()).strip()
        if clean:
            normalized.add(f"<{clean}>")
    return normalized

def extract_mgrs(text):
    """
    Extracts MGRS coordinates from text (case-insensitive).
    """
    if not text:
        return set()
    unescaped = html.unescape(text)
    pattern = r'\b\d{1,2}[A-Za-z]{3}\d{4,12}\b'
    return set(re.findall(pattern, unescaped))

def extract_latlon(text):
    """
    Extracts Lat/Lon coordinates from text (case-insensitive).
    """
    if not text:
        return set()
    unescaped = html.unescape(text)
    pattern = r'\b\d+(?:\.\d+)?\s*[NSns]\s*,?\s*\d+(?:\.\d+)?\s*[EWew]\b'
    return set(re.findall(pattern, unescaped))

def check_already_posted(vessel_identifier):
    """
    Scrapes the target room (indopacom-third-room) to check if the vessel identifier
    has already been posted.
    """
    data = get_messages("indopacom-third-room")
    if not data or "messages" not in data:
        return False
    for msg in data["messages"]:
        text = html.unescape(msg.get("text", ""))
        if vessel_identifier in text:
            return True
    return False

def initialize_posted_vessels():
    """
    Initializes the in-memory cache of posted vessel identifiers by checking history.
    """
    print("Initializing posted vessels cache from indopacom-third-room history...")
    data = get_messages("indopacom-third-room")
    if data and "messages" in data:
        for msg in data["messages"]:
            text = msg.get("text", "")
            found = extract_vessel_identifiers(text)
            for vessel in found:
                posted_vessels.add(vessel)
    print(f"Initialized Cache. Already posted vessels: {posted_vessels}")

def determine_classification(msg1, msg2):
    """
    Determines classification based on the messages' classifications.
    """
    c1 = msg1.get("classification", "UNCLASSIFIED")
    c2 = msg2.get("classification", "UNCLASSIFIED")
    if "SECRET" in c1 or "SECRET" in c2:
        return "SECRET"
    if "CONFIDENTIAL" in c1 or "CONFIDENTIAL" in c2:
        return "CONFIDENTIAL"
    if "FOUO" in c1 or "FOUO" in c2:
        return "UNCLASSIFIED//FOUO"
    return "UNCLASSIFIED"

def main():
    print("Starting indopacom room message merger bot...")
    initialize_posted_vessels()
    
    # Track the last message IDs processed from each room to avoid reprocessing the same state
    # unless a new message is received.
    last_processed_ids = {"indopacom-bda-messages": None, "indopacom-coord": None}

    while True:
        try:
            # Scrape the most recent message from both rooms
            msg_bda = get_most_recent_message("indopacom-bda-messages")
            msg_coord = get_most_recent_message("indopacom-coord")
            
            if msg_bda and msg_coord:
                bda_id = msg_bda.get("id")
                coord_id = msg_coord.get("id")
                
                # Check if we have a new pair of messages or if the latest messages have changed
                if (bda_id != last_processed_ids["indopacom-bda-messages"] or 
                    coord_id != last_processed_ids["indopacom-coord"]):
                    
                    last_processed_ids["indopacom-bda-messages"] = bda_id
                    last_processed_ids["indopacom-coord"] = coord_id
                    
                    bda_text = msg_bda.get("text", "")
                    coord_text = msg_coord.get("text", "")
                    
                    bda_vessels = extract_vessel_identifiers(bda_text)
                    coord_vessels = extract_vessel_identifiers(coord_text)
                    
                    # Find intersection (talking about the same item/ship/vessel/object)
                    common_vessels = bda_vessels.intersection(coord_vessels)
                    
                    for vessel in common_vessels:
                        # Check in-memory cache first
                        if vessel not in posted_vessels:
                            # Double check the API history to be absolutely sure
                            if not check_already_posted(vessel):
                                # Determine classification
                                classification = determine_classification(msg_bda, msg_coord)
                                
                                # Extract coordinates from both messages combined
                                combined_text = f"{bda_text}\n{coord_text}"
                                mgrs_coords = sorted(list(extract_mgrs(combined_text)))
                                latlon_coords = sorted(list(extract_latlon(combined_text)))
                                
                                mgrs_str = ", ".join(mgrs_coords) if mgrs_coords else "Not found"
                                latlon_str = ", ".join(latlon_coords) if latlon_coords else "Not found"
                                
                                # Format the message to only have the vessel name and coordinates in both mgrs and lat lon
                                combined_message = (
                                    f"Vessel: {vessel}\n"
                                    f"MGRS: {mgrs_str}\n"
                                    f"Lat/Lon: {latlon_str}"
                                )
                                
                                print(f"Match found for {vessel}. Posting to indopacom-third-room...")
                                send_public_message(
                                    message_text=combined_message,
                                    roomName="indopacom-third-room",
                                    session_id="",  # Session is deprecated and not required as per cs-docs.txt
                                    classification=classification
                                )
                                
                                # Add to in-memory set
                                posted_vessels.add(vessel)
                            else:
                                # Update cache if it was already posted in history
                                posted_vessels.add(vessel)
                                
        except Exception as e:
            print(f"[Error] Error in main loop: {e}", file=sys.stderr)
            
        time.sleep(10)

if __name__ == "__main__":
    main()
