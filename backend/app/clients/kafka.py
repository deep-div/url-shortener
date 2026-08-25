import ssl
from app.core.config import settings

def build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(cadata=settings.KAFKA_CA_CERT.replace("\\n", "\n"))
    return ctx


kafka_client = {
    "bootstrap_servers": settings.KAFKA_SERVICE_URI,
    "security_protocol": "SASL_SSL",
    "sasl_mechanism": "SCRAM-SHA-256",
    "sasl_plain_username": settings.KAFKA_USERNAME,
    "sasl_plain_password": settings.KAFKA_PASSWORD,
    "ssl_context": build_ssl_context(),
}
