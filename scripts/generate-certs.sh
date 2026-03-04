#!/bin/sh
set -e

DOMAIN="${STAXREAD_DOMAIN:-localhost}"
ALGO="${CERT_ALGO:-EC}"
KEY_PARAM="${CERT_KEY_PARAM:-prime256v1}"
DAYS="${CERT_DAYS:-365}"
COUNTRY="${CERT_COUNTRY:-US}"
ORG="${CERT_ORG:-StaxRead}"
EXTRA_SANS="${CERT_EXTRA_SANS:-}"
CERT_FILE="/certs/cert.pem"
KEY_FILE="/certs/key.pem"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates already exist, skipping generation."
    exit 0
fi

mkdir -p /certs

# Determine primary Subject Alternative Name: IP address or DNS hostname
if echo "$DOMAIN" | grep -qE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'; then
    PRIMARY_SAN="IP:${DOMAIN}"
else
    PRIMARY_SAN="DNS:${DOMAIN}"
fi

# Append any extra SANs
if [ -n "$EXTRA_SANS" ]; then
    SAN_LIST="${PRIMARY_SAN},${EXTRA_SANS}"
else
    SAN_LIST="${PRIMARY_SAN}"
fi

SUBJ="/C=${COUNTRY}/O=${ORG}/CN=${DOMAIN}"

echo "Generating self-signed certificate for '${DOMAIN}' (algo: ${ALGO}, validity: ${DAYS} days)..."

if [ "$ALGO" = "EC" ]; then
    openssl req -x509 -nodes \
        -newkey ec \
        -pkeyopt "ec_paramgen_curve:${KEY_PARAM}" \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -days "$DAYS" \
        -subj "$SUBJ" \
        -addext "subjectAltName=${SAN_LIST}" \
        2>/dev/null
else
    openssl req -x509 -nodes \
        -newkey "rsa:${KEY_PARAM}" \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -days "$DAYS" \
        -subj "$SUBJ" \
        -addext "subjectAltName=${SAN_LIST}" \
        2>/dev/null
fi

chmod 600 "$KEY_FILE"
echo "Certificate written to ${CERT_FILE}"
