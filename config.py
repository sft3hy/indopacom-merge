import os

CS_HOST = "chatsurfer.nro.mil"
TEST = os.environ["TEST_LOCAL"]
CHATKEY = os.environ["CHATKEY"]
BOTNAME = "slammy"

if TEST == "True":
    CERT_PATH = "/Users/samueltownsend/dev/certs/justcert.pem"
    KEY_PATH = "/Users/samueltownsend/dev/certs/decrypted.key"
    CA_BUNDLE_PATH = "/Users/samueltownsend/dev/certs/dod_CAs.pem"
    MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    MODEL_PRETTY = "Lamma 4 Scout (via https://groq.com)"
    MODEL_PROVIDER = "groq"

else:
    CERT_PATH = "/config/justcert.crt"  # /etc/rancher/ssl/npe/tls.crt"
    KEY_PATH = "/config/decrypted.key"  # /etc/rancher/ssl/npe/tls.key"
    CA_BUNDLE_PATH = "/config/dod_CA.pem"  # /etc/rancher/ssl/ca/ca-bundle"  # Path is mountPath + keyName
    MODEL = "bedrock-claude-3-5-sonnet-v1"
    MODEL_PRETTY = "Claude 3.5 Sonnet (via https://sanctuary.i2cv.io)"
    MODEL_PROVIDER = "bedrock"
