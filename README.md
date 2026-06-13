# indopacom-merge

A Python-based Kubernetes daemon that monitors and merges intelligence messages from ChatSurfer chatrooms.

## Overview

The `indopacom-merge` bot monitors two source ChatSurfer rooms:
1. `indopacom-bda-messages` (Battle Damage Assessment)
2. `indopacom-coord` (Coordination)

Every 10 seconds, it polls the single most recent message from each room. If both messages are talking about the same item (matching on a vessel identifier in the format `<vessel_name vessel_number>`), and a tip for that vessel has not yet been posted to `indopacom-third-room`, the bot publishes a consolidated tip to that room.

The output tip contains only the vessel name and coordinates parsed in both MGRS and Lat/Lon formats.

## Key Features

- **Continuous Polling**: Checks room status every 10 seconds via ChatSurfer REST APIs.
- **HTML Entity Decoding**: Automatically unescapes HTML entities (e.g. `&lt;` and `&gt;` back to `<` and `>`) to ensure robust regex matching.
- **Coordinate Extraction**: Parses combined messages to extract coordinates in:
  - **MGRS** format (e.g., `50RQN52150600`)
  - **Lat/Lon** format (e.g., `24.44715286N 119.48723514E` or `35.2917N 139.6722E`)
- **Deduplication & Restart Resilience**:
  - Automatically reads the destination room (`indopacom-third-room`) history at startup to populate an in-memory cache of already-posted vessels.
  - Double-checks the live API history before posting any new tip to prevent duplicate reports in multi-bot setups.

## Code Structure

- [enchilada.py](file:///Users/samueltownsend/dev/cosmic/indopacom-merge/enchilada.py): Main entrypoint containing the continuous polling loop, match checking, coordinate extraction, and deduplication logic.
- [config.py](file:///Users/samueltownsend/dev/cosmic/indopacom-merge/config.py): Environment-based configuration parameters (CS host, credentials, SSL paths).
- [cs_helpers.py](file:///Users/samueltownsend/dev/cosmic/indopacom-merge/cs_helpers.py): REST API client helpers for sending messages.

---

## Deployment

### Local Development

1. Set up a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install requests
   ```
2. Configure your environment variables:
   ```bash
   export TEST_LOCAL="True"
   export CHATKEY="your_api_key_here"
   ```
3. Run the bot:
   ```bash
   PYTHONPATH=. python3 -u enchilada.py
   ```

### Containerization (Docker)

To build the Docker image locally:
```bash
docker build -t harbor.i2cv.io/cosmichorizon/indopacom-merge:1.0.0 .
```

### Kubernetes Deployment (Helm)

The application is deployed using the Helm chart situated in the `chart/` directory.

#### Certs Secrets Requirements
In production (`TEST_LOCAL="False"`), the bot expects TLS credentials to be mounted into `/config/`. The Helm chart handles this by mounting a Secret containing the keys:
- `/config/justcert.crt`
- `/config/decrypted.key`
- `/config/dod_CA.pem`

#### Deploying with Helm
1. Create the secret containing your ChatSurfer API key:
   ```bash
   kubectl create secret generic indopacom-merge-secrets --from-literal=chatkey="<your_chatkey>"
   ```
2. Create the secret containing your TLS certificates:
   ```bash
   kubectl create secret generic indopacom-merge-certs \
     --from-file=justcert.crt=/path/to/cert.crt \
     --from-file=decrypted.key=/path/to/decrypted.key \
     --from-file=dod_CA.pem=/path/to/ca.pem
   ```
3. Install the Helm chart:
   ```bash
   helm install indopacom-merge ./chart
   ```
