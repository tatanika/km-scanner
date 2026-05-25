#!/usr/bin/env python3
"""
HTTPS-сервер для КМ Сканера.
Камера в браузере работает ТОЛЬКО через HTTPS (или localhost).
Этот скрипт создаёт самоподписанный сертификат и запускает HTTPS на порту 8443.
"""
import os, sys, ssl, socket, subprocess

PORT = 8443
BASE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(BASE, '_cert.pem')
KEY  = os.path.join(BASE, '_key.pem')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def make_cert():
    if os.path.exists(CERT) and os.path.exists(KEY):
        print('[cert] Сертификат уже есть, использую его.')
        return True
    print('[cert] Создаю самоподписанный сертификат...')
    try:
        ip = get_local_ip()
        # Try openssl
        result = subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', KEY, '-out', CERT,
            '-days', '365', '-nodes',
            '-subj', f'/CN={ip}',
            '-addext', f'subjectAltName=IP:{ip},IP:127.0.0.1'
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print('[cert] OK')
            return True
        else:
            print('[cert] openssl error:', result.stderr[:200])
            return False
    except FileNotFoundError:
        print('[cert] openssl не найден, пробую через Python cryptography...')
        return make_cert_python()

def make_cert_python():
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime, ipaddress
        ip = get_local_ip()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, ip)])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.IPv4Address(ip)),
                x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
            ]), critical=False)
            .sign(key, hashes.SHA256())
        )
        with open(KEY, 'wb') as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))
        with open(CERT, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print('[cert] OK (через Python cryptography)')
        return True
    except ImportError:
        print('[cert] Нужна библиотека: pip install cryptography')
        return False
    except Exception as e:
        print(f'[cert] Ошибка: {e}')
        return False

def main():
    if not make_cert():
        print()
        print('Не удалось создать сертификат.')
        print('Альтернатива: задеплой на GitHub Pages (HTTPS бесплатно).')
        input('Enter для выхода...')
        return

    ip = get_local_ip()

    import http.server
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=BASE, **kw)
        def log_message(self, fmt, *args):
            print(f'  [{args[0]}] {args[1]}')

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)

    httpd = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    print()
    print('=' * 50)
    print('  KM Scanner — HTTPS Server')
    print('=' * 50)
    print(f'  Local:   https://localhost:{PORT}')
    print(f'  Network: https://{ip}:{PORT}')
    print()
    print('  ВАЖНО: при первом открытии браузер покажет')
    print('  предупреждение "небезопасно" — нажми')
    print('  "Дополнительно" -> "Перейти на сайт" (или аналог).')
    print()
    print('  Ctrl+C для остановки.')
    print('=' * 50)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nСервер остановлен.')

if __name__ == '__main__':
    main()
