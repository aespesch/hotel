"""
Configuration file for the hotel reservation system.
This centralizes all settings that might need to be changed without modifying the main code.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (for sensitive data)
load_dotenv()

# System Information
SYSTEM_NAME = "Sistema de Reservas - T90 35 Anos"
EVENT_NAME = "T90 - 35 Anos - Almoço Comemorativo"
EVENT_DATE = "28 a 30 de novembro de 2025 (2 diárias com café da manhã)"
EVENT_LOCATION = "Hotel Ibis Colinas/Mercure São José dos Campos"

# PIX Payment Configuration
# IMPORTANT: Never commit your actual PIX key to GitHub!
# Use environment variables for production
PIX_KEY = os.getenv("PIX_KEY", "toni@ita90.com.br")  # Your PIX key
PIX_MERCHANT_NAME = os.getenv("PIX_MERCHANT_NAME", "Antônio Magno Lima Espeschit")
PIX_CITY = os.getenv("PIX_CITY", "São José dos Campos-SP")

# Data Source Configuration
# Path to the CSV files
PARTICIPANTS_FILE = "participants.csv"
ROOMS_FILE = "rooms.csv"

# User Interface Messages
MESSAGES = {
    "welcome": f"Bem-vindo ao {SYSTEM_NAME}!",
    "not_found": "Nome não encontrado na lista. Verifique se digitou corretamente ou entre em contato com a organização.",
    "payment_instructions": """
    **Instruções para pagamento:**
    1. Abra o aplicativo do seu banco
    2. Acesse a opção PIX
    3. Escaneie o QR Code acima ou copie o código
    4. Confirme o pagamento
    
    IMPORTANTE: Não precisa mandar o comprovante via whatsapp!
    
    **Após o pagamento:**
    - Seu nome vai aparecer na lista do grupo T90 Festas.
    """,
    "confirmation_email_subject": f"Confirmação de reserva - {SYSTEM_NAME}"
}

# Application Settings
# Page configuration for Streamlit
PAGE_CONFIG = {
    "page_title": f"Reservas - {EVENT_NAME}",
    "page_icon": "🏨",
    "layout": "centered",
    "initial_sidebar_state": "collapsed"
}

# Admin Configuration
# Password for accessing the admin dashboard
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Change this!

# Feature Flags
# Enable or disable features during development
FEATURES = {
    "send_emails": False,  # Set to True when email is configured
    "validate_payment": False,  # Set to True when payment API is integrated
    "admin_dashboard": True,  # Enable admin view
    "export_data": True  # Allow data export to CSV
}