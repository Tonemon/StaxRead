#!/bin/sh
set -e

DOMAIN="${STAXREAD_DOMAIN:-localhost}"
CERT_FILE="/certs/cert.pem"
KEY_FILE="/certs/key.pem"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates already exist, skipping generation."
    exit 0
fi

mkdir -p /certs

# Determine Subject Alternative Name: IP address or DNS hostname
if echo "$DOMAIN" | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'; then
    SAN="IP:${DOMAIN}"
else
    SAN="DNS:${DOMAIN}"
fi

echo "Generating self-signed certificate for '${DOMAIN}' (SAN: ${SAN}, validity: 365 days)..."

openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days 365 \
    -subj "/CN=${DOMAIN}/O=StaxRead" \
    -addext "subjectAltName=${SAN}" \
    2>/dev/null

chmod 600 "$KEY_FILE"
echo "Certificate written to ${CERT_FILE}"
