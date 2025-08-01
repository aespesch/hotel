"""
Configuration file for the hotel reservation system.
This centralizes all settings that might need to be changed without modifying the main code.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (for sensitive data)
load_dotenv()

# Event Information
EVENT_NAME = "Sistema de Reservas de Hotel - T90"
EVENT_DATE = "28-30 de novembro de 2025"
EVENT_LOCATION = "São José dos Campos - SP"

# Data Source Configuration
PARTICIPANTS_FILE = "participants.csv"
ROOMS_FILE = "rooms.csv"

# PIX Payment Configuration
# IMPORTANT: Never commit your actual PIX key to GitHub!
# Use environment variables for production
PIX_KEY = os.getenv("PIX_KEY", "toni@ita90.com.br")  # Your PIX key
PIX_MERCHANT_NAME = os.getenv("PIX_MERCHANT_NAME", "Antônio Magno Lima Espeschit")
PIX_CITY = os.getenv("PIX_CITY", "São José dos Campos-SP")

# User Interface Messages
MESSAGES = {
    "welcome": f"Bem-vindo ao sistema de reservas de hotel!",
    "not_found": "Nome não encontrado na lista. Verifique se digitou corretamente ou entre em contato com a organização.",
    "payment_instructions": """
    **Instruções para pagamento:**
    1. Abra o aplicativo do seu banco
    2. Acesse a opção PIX
    3. Escaneie o QR Code acima
    4. Confirme o pagamento
    
    IMPORTANTE: Não precisa mandar o comprovante via whatsapp!
    """,
    "confirmation_email_subject": f"Confirmação de reserva - Hotel T90"
}

# Application Settings
# Page configuration for Streamlit
PAGE_CONFIG = {
    "page_title": f"Reservas de Hotel - T90",
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