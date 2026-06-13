import time
import requests
from config import *


def send_public_message(
    message_text: str,
    roomName: str,
    session_id: str,
    classification: str = "UNCLASSIFIED//FOUO",
    domainId: str = "chatsurferxmppunclass",
    nickName: str = "indopacom_merge_bot",
):
    headers = {
        "Content-type": "application/json",
    }
    if TEST == "True":
        nickName = "indopacom_merge_bot_local"
    message = {
        "classification": classification,
        "message": message_text,
        "domainId": domainId,
        "nickName": nickName,
        "roomName": roomName,
    }
    cook = {"SESSION": session_id}

    url = "https://" + CS_HOST + "/api/chatserver/message?api-key=" + CHATKEY

    send = requests.post(
        url,
        cert=(CERT_PATH, KEY_PATH),
        verify=CA_BUNDLE_PATH,
        headers=headers,
        json=message,
        cookies=cook,
    )
    print(f"Response from ChatSurfer send public message: {send}")
