#!/usr/bin/env python3
"""
Script de teste para verificar conexão SMTP e validade de credenciais
"""
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

print(f"Testando conexão SMTP...")
print(f"Servidor: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Email: {EMAIL_FROM[:10]}***")

try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    print("✓ Conexão iniciada com sucesso")
    
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    print("✓ Autenticação bem-sucedida!")
    
    server.quit()
    print("\n✓ Testes passaram! Email está configurado corretamente.")
    
except smtplib.SMTPAuthenticationError:
    print("\n✗ Erro de autenticação!")
    print("Verifique:")
    print("  1. Google App Password (https://myaccount.google.com/apppasswords)")
    print("  2. Confirmou a senha de 16 caracteres no .env?")
    print("  3. EMAIL_FROM está correto?")
    
except smtplib.SMTPException as e:
    print(f"\n✗ Erro SMTP: {e}")
    
except Exception as e:
    print(f"\n✗ Erro: {e}")
