"""Generate a self-signed cert for local dev (HTTPS + WebRTC getUserMedia)."""
import datetime
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# ---- EDIT THIS: your LAN IP (from ipconfig) ------------------------------
LAN_IP = "10.88.204.161"
LAN_IP = "10.88.204.161"
DAYS = 825
# --------------------------------------------------------------------------

hostname = socket.gethostname()

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, LAN_IP),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VoiceChat Dev"),
])

san = x509.SubjectAlternativeName([
    x509.DNSName("localhost"),
    x509.DNSName(hostname),
    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    x509.IPAddress(ipaddress.ip_address("192.168.1.2")),
    x509.IPAddress(ipaddress.ip_address(LAN_IP)),
])



now = datetime.datetime.now(datetime.timezone.utc)
cert = (
    x509.CertificateBuilder()
    .subject_name(subject).issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - datetime.timedelta(days=1))
    .not_valid_after(now + datetime.timedelta(days=DAYS))
    .add_extension(san, critical=False)
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(key, hashes.SHA256())
)

Path("key.pem").write_bytes(key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
))
Path("cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))

print(f"Wrote cert.pem + key.pem")
print(f"  CN       : {LAN_IP}")
print(f"  SAN      : localhost, {hostname}, 127.0.0.1, {LAN_IP}")
print(f"  Valid    : {DAYS} days")
print()
print("Run the server with:")
print(f"  python server.py --port 8443 --ssl-keyfile key.pem --ssl-certfile cert.pem")
print(f"Then open:  https://{LAN_IP}:8443")