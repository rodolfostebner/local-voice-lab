
import os
import socket
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

CERT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'certs'))
CERT_FILE = os.path.join(CERT_DIR, 'cert.pem')
KEY_FILE = os.path.join(CERT_DIR, 'key.pem')

def get_local_ip():
    # Prioridade para o IP real da máquina na LAN
    return "192.168.68.110"

def generate_self_signed_cert():
    print("[TLS] Gerando certificados auto-assinados para LAN...")
    os.makedirs(CERT_DIR, exist_ok=True)

    local_ip = get_local_ip()
    print(f"[TLS] IP Detectado: {local_ip}")

    # Gerar chave privada
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Configurar o nome do certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Santa Catarina"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Blumenau"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Rudy AI Labs"),
        x509.NameAttribute(NameOID.COMMON_NAME, local_ip),
    ])

    # Adicionar Subject Alternative Names (SAN) para localhost e o IP local
    import ipaddress
    san = x509.SubjectAlternativeName([
        x509.DNSName(u"localhost"),
        x509.IPAddress(ipaddress.ip_address(local_ip)),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Válido por 1 ano
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        san, critical=False
    ).sign(key, hashes.SHA256())

    # Salvar chave
    with open(KEY_FILE, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Salvar certificado
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[TLS] Certificados gerados em: {CERT_DIR}")
    print(f"[TLS] Certificado: {CERT_FILE}")
    print(f"[TLS] Chave: {KEY_FILE}")
    print("\nAVISO: No celular, voce precisará aceitar o 'Risco de Segurança' (Self-Signed) para habilitar o microfone.")

if __name__ == "__main__":
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        generate_self_signed_cert()
    else:
        print(f"[TLS] Certificados já existem em {CERT_DIR}. Use --force para sobrescrever (não implementado).")
