"""
Hotel Reservation System - Main Application
A complete web system for managing hotel room reservations.
"""

import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64
import os
from datetime import datetime
import unicodedata
import re
import uuid
import crcmod
from difflib import SequenceMatcher
from config import *


# Page configuration
st.set_page_config(**PAGE_CONFIG)

# Initialize session state
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'participant_data' not in st.session_state:
    st.session_state.participant_data = None
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False
if 'room_selections' not in st.session_state:
    st.session_state.room_selections = {}
if 'total_amount' not in st.session_state:
    st.session_state.total_amount = 0
if 'observations' not in st.session_state:
    st.session_state.observations = ""
if 'show_observations' not in st.session_state:
    st.session_state.show_observations = False

def normalize_name(name):
    """
    Normalize name for comparison by removing accents, extra spaces, 
    and converting to lowercase.
    """
    # If name is not a string, return empty string
    if not isinstance(name, str):
        return ""
    
    # Remove leading/trailing spaces
    name = name.strip()
    
    if name == "":
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Normalize to decomposed form and remove accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    
    # Remove non-alphanumeric characters except spaces
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    return name

def fuzzy_match(str1, str2, threshold=0.85):
    """Check if two strings match with a given similarity threshold."""
    return SequenceMatcher(None, str1, str2).ratio() >= threshold

def is_abbreviation_match(input_name, db_name):
    """Check if input_name could be an abbreviation of db_name."""
    input_parts = input_name.split()
    db_parts = db_name.split()
    
    # If input has more parts than database name, it can't be an abbreviation
    if len(input_parts) > len(db_parts):
        return False
    
    # Check if all input parts match the beginning of corresponding db parts
    for i, input_part in enumerate(input_parts):
        if not db_parts[i].startswith(input_part):
            return False
    
    return True

def load_participants():
    """Load participants from CSV file."""
    try:
        # Try common encodings for Portuguese
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(PARTICIPANTS_FILE, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        if df is None:
            st.error("❌ Não foi possível carregar o arquivo com nenhuma codificação testada.")
            return pd.DataFrame()
        
        return df
    
    except FileNotFoundError:
        st.error(f"❌ Arquivo não encontrado: {PARTICIPANTS_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro inesperado ao carregar o arquivo: {str(e)}")
        return pd.DataFrame()

def load_rooms():
    """Load room types from CSV file."""
    try:
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(ROOMS_FILE, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            st.error("❌ Não foi possível carregar o arquivo de quartos.")
            return pd.DataFrame()
        
        return df
    
    except FileNotFoundError:
        st.error(f"❌ Arquivo não encontrado: {ROOMS_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar quartos: {str(e)}")
        return pd.DataFrame()

def find_participant(name, participants_df):
    """Find participant with flexible name matching."""
    normalized_input = normalize_name(name)
    
    if participants_df.empty:
        st.warning("⚠️ A lista de participantes está vazia.")
        return None
    
    best_match = None
    best_score = 0
    
    for idx, row in participants_df.iterrows():
        if 'full_name' in row:
            original_db_name = row['full_name']
            normalized_db_name = normalize_name(original_db_name)
            
            # Exact match
            if normalized_input == normalized_db_name:
                return row
            
            # Check for abbreviation match
            if is_abbreviation_match(normalized_input, normalized_db_name):
                return row
            
            # Fuzzy match for typos
            score = SequenceMatcher(None, normalized_input, normalized_db_name).ratio()
            if score > best_score and score >= 0.85:
                best_score = score
                best_match = row
    
    if best_match is not None:
        st.success(f"✅ Correspondência encontrada para: {best_match['full_name']}")
        return best_match
    
    st.warning("⚠️ Nenhuma correspondência encontrada na lista de participantes.")
    return None

def calculate_total(room_selections, rooms_df):
    """Calculate total amount based on room selections."""
    total = 0
    for room_id, quantity in room_selections.items():
        if quantity > 0:
            room = rooms_df[rooms_df['id'] == room_id].iloc[0]
            total += quantity * room['value']
    return total

def generate_emv_code(key, amount, merchant_name, city, tx_id=None):
    """Generate 100% valid PIX EMV code following Brazilian Central Bank specs"""
    # Helper function to sanitize and format text
    def format_text(text, max_length, remove_accents=True):
        if remove_accents:
            # Remove accents
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if not unicodedata.combining(c))
        # Keep spaces and basic punctuation for readability
        text = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', text)
        # Truncate to max length
        return text[:max_length]
    
    # Format amount with ALWAYS 2 decimal places
    amount_str = f"{amount:.2f}"
    
    # Clean the PIX key (remove spaces and special chars)
    clean_key = re.sub(r'[^a-zA-Z0-9@\.\-]', '', key)
    
    # Sanitize merchant name and city
    sanitized_merchant = format_text(merchant_name, 25, remove_accents=True).upper()
    sanitized_city = format_text(city, 15, remove_accents=True).upper()
    
    # Build payload components
    payload = "000201"  # Payload format indicator
    
    # Merchant Account Information (26)
    gui = "BR.GOV.BCB.PIX"
    # Format: 0014BR.GOV.BCB.PIX + 01 + key length + key
    pix_key_field = f"01{len(clean_key):02d}{clean_key}"
    pix_data = f"0014{gui}{pix_key_field}"
    payload += f"26{len(pix_data):02d}{pix_data}"
    
    # Merchant Category Code (52)
    mcc = "0000"
    payload += f"52{len(mcc):02d}{mcc}"
    
    # Transaction Currency (53)
    currency = "986"  # BRL
    payload += f"53{len(currency):02d}{currency}"
    
    # Transaction Amount (54) - only include if amount > 0
    if amount > 0:
        payload += f"54{len(amount_str):02d}{amount_str}"
    
    # Country Code (58)
    country = "BR"
    payload += f"58{len(country):02d}{country}"
    
    # Merchant Name (59)
    payload += f"59{len(sanitized_merchant):02d}{sanitized_merchant}"
    
    # Merchant City (60)
    payload += f"60{len(sanitized_city):02d}{sanitized_city}"
    
    # Additional Data Field (62) - Transaction ID
    if tx_id and tx_id != "***":
        tx_field = f"05{len(tx_id):02d}{tx_id}"
        payload += f"62{len(tx_field):02d}{tx_field}"
    else:
        # Generate a unique transaction ID
        unique_id = f"PIX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        tx_field = f"05{len(unique_id):02d}{unique_id}"
        payload += f"62{len(tx_field):02d}{tx_field}"
    
    # Add CRC placeholder
    payload += "6304"
    
    # Calculate CRC16-CCITT
    crc16 = crcmod.predefined.Crc('crc-ccitt-false')
    crc16.update(payload.encode('utf-8'))
    crc_value = format(crc16.crcValue, '04X')
    
    return payload + crc_value

def generate_pix_qr_code(amount, participant_name, participant_id=None, tx_id=None):
    """Generate PIX QR Code for payment with participant ID comment"""
    # Generate a unique transaction ID with participant ID comment
    if not tx_id:
        # Add participant ID as comment in transaction ID format: HHNNHH
        if participant_id is not None and str(participant_id).strip() != '':
            tx_id = f"HH{participant_id}HH"
        else:
            # Fallback to unique transaction ID if no participant ID
            tx_id = f"HTL{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    
    # Pass transaction ID with participant ID comment
    pix_payload = generate_emv_code(
        PIX_KEY,
        amount,
        PIX_MERCHANT_NAME,
        PIX_CITY,
        tx_id=tx_id
    )
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(pix_payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buf = BytesIO()
    img.save(buf, format='PNG')
    byte_img = buf.getvalue()
    
    return byte_img, pix_payload

def save_reservation(participant_data, room_selections, total_amount, observations, rooms_df):
    """Save reservation to CSV file."""
    # Create data directory if it doesn't exist
    os.makedirs('./data', exist_ok=True)
    
    reservation_id = str(uuid.uuid4())[:8]
    
    # Build room details string
    room_details = []
    for room_id, quantity in room_selections.items():
        if quantity > 0:
            room = rooms_df[rooms_df['id'] == room_id].iloc[0]
            room_details.append(f"{room['hotel']} {room['type'].upper()}: {quantity}")
    
    reservation_data = {
        'reservation_id': reservation_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'participant_name': participant_data['full_name'],
        'participant_id': participant_data.get('id', ''),
        'room_details': '; '.join(room_details),
        'total_amount': total_amount,
        'observations': observations,
        'payment_status': 'pending'
    }
    
    # Check if file exists
    file_path = './data/RESERVAS.CSV'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = pd.concat([df, pd.DataFrame([reservation_data])], ignore_index=True)
    else:
        df = pd.DataFrame([reservation_data])
    
    df.to_csv(file_path, index=False)
    
    return reservation_id

def show_room_selection():
    """Show the room selection interface."""
    participant = st.session_state.participant_data
    
    st.markdown(f"### Bem-vindo(a), {participant['full_name']}! 👋")
    
    # Show lunch participants if applicable
    if participant.get('participants', 0) > 0:
        st.info(f"**Participantes do almoço na Churrascaria Boigalê:** {participant['participants']}")
    
    # Load rooms
    rooms_df = load_rooms()
    if rooms_df.empty:
        st.error("Erro ao carregar informações dos quartos.")
        return
    
    st.markdown("### 🏨 Seleção de Quartos")
    
    # Room type explanations
    st.markdown("""
    **Tipos de Quarto:**
    - **DBL**: Quarto para 2 pessoas com 1 cama de casal ou 2 de solteiro
    - **SGL**: Quarto para 1 pessoa com 1 cama de casal ou 2 de solteiro
    
    **Informações importantes:**
    - Check-In: Sexta-Feira 28NOV2025 14:00
    - Check-Out: Sábado 30NOV2025 14:00
    - Café da manhã incluído
    - Estacionamento não incluído
    - Se precisar de algo diferente, use o campo observações
    """)
    
    st.markdown("---")
    
    # Room selection interface
    room_selections = {}
    total = 0
    
    # Group rooms by hotel
    hotels = rooms_df['hotel'].unique()
    
    for hotel in hotels:
        st.markdown(f"#### Hotel {hotel.title()}")
        hotel_rooms = rooms_df[rooms_df['hotel'] == hotel]
        
        cols = st.columns(len(hotel_rooms))
        
        for idx, (_, room) in enumerate(hotel_rooms.iterrows()):
            with cols[idx]:
                st.markdown(f"**{room['type'].upper()}**")
                st.markdown(f"R\\$ {room['value']:.2f}")
                quantity = st.number_input(
                    "Quantidade:",
                    min_value=0,
                    max_value=10,
                    value=st.session_state.room_selections.get(room['id'], 0),
                    key=f"room_{room['id']}"
                )
                room_selections[room['id']] = quantity
                total += quantity * room['value']
    
    # Update session state
    st.session_state.room_selections = room_selections
    st.session_state.total_amount = total
    
    # Show total
    st.markdown("---")
    st.markdown(f"### 💰 Valor Total: R$ {total:.2f}")
    
    # Check if at least one room is selected
    has_selection = any(q > 0 for q in room_selections.values())
    
    if has_selection:
        if st.button("Prosseguir", type="primary"):
            st.session_state.show_observations = True
            st.rerun()
    else:
        st.warning("Selecione pelo menos um quarto para prosseguir.")

def show_observations_page():
    """Show the observations page."""
    st.markdown("### 📝 Observações (Opcional)")
    
    observations = st.text_area(
        "Se precisar de algo especial (cama extra, acessibilidade, etc.), informe aqui:",
        value=st.session_state.observations,
        height=100,
        placeholder="Ex: Preciso de quarto no térreo por problemas de locomoção"
    )
    
    st.session_state.observations = observations
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Voltar", type="secondary"):
            st.session_state.show_observations = False
            st.rerun()
    
    with col2:
        if st.button("Confirmar e Gerar Pagamento", type="primary"):
            st.session_state.show_payment = True
            st.rerun()

def show_payment_page():
    """Show the payment page with QR code."""
    participant = st.session_state.participant_data
    room_selections = st.session_state.room_selections
    total_amount = st.session_state.total_amount
    observations = st.session_state.observations
    
    st.markdown(f"### 💳 Pagamento - {participant['full_name']}")
    st.markdown("---")
    
    # Load rooms for details
    rooms_df = load_rooms()
    
    # Save reservation
    reservation_id = save_reservation(participant, room_selections, total_amount, observations, rooms_df)
    
    # Generate QR Code
    participant_id = participant.get('id', '')
    qr_img, pix_payload = generate_pix_qr_code(total_amount, participant['full_name'], participant_id)
    
    # Display QR Code
    st.markdown("### 📱 QR Code PIX")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, width=300)
    
    # Display PIX copy code
    st.markdown("### 📋 Código PIX Copia e Cola")
    st.markdown("Clique no botão de copiar no canto direito do campo abaixo:")
    st.code(pix_payload, language=None)
    
    # Display reservation summary
    st.markdown("### 📊 Resumo da Reserva")
    
    for room_id, quantity in room_selections.items():
        if quantity > 0:
            room = rooms_df[rooms_df['id'] == room_id].iloc[0]
            st.markdown(f"- **{room['hotel'].title()} {room['type'].upper()}:** {quantity} × R\\$ {room['value']:.2f} = R\\$ {quantity * room['value']:.2f}")
    
    if observations:
        st.markdown(f"**Observações:** {observations}")
    
    st.markdown(f"### 💰 **Total a pagar: R$ {total_amount:.2f}**")
    
    st.markdown("---")
    
    # Payment instructions
    st.markdown(MESSAGES['payment_instructions'])
    
    # Confirmation details
    st.success(f"✅ Reserva registrada! ID: {reservation_id}")
    
    # Navigation button
    if st.button("Nova Reserva", type="primary"):
        # Reset all session state
        st.session_state.confirmed = False
        st.session_state.participant_data = None
        st.session_state.show_payment = False
        st.session_state.room_selections = {}
        st.session_state.total_amount = 0
        st.session_state.observations = ""
        st.session_state.show_observations = False
        st.rerun()

def main():
    """Main application flow."""
    # Custom CSS
    st.markdown("""
    <style>
    .event-title {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: rgb(9, 171, 59) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }
    @media (max-width: 768px) {
        .event-title {
            font-size: 1.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display title
    st.markdown(f'<h1 class="event-title">🏨 {SYSTEM_NAME}</h1>', unsafe_allow_html=True)
    
    st.markdown(f"📅 **Data do Evento:** {EVENT_DATE}")
    st.markdown(f"📍 **Local:** {EVENT_LOCATION}")
    st.markdown("---")
    
    # Load participants
    participants_df = load_participants()
    
    if participants_df.empty:
        st.error("Lista de participantes vazia ou não carregada")
        return
    
    # Check which page to show
    if st.session_state.show_payment:
        show_payment_page()
    elif st.session_state.show_observations:
        show_observations_page()
    elif st.session_state.confirmed:
        show_room_selection()
    else:
        # Step 1: Name verification
        st.markdown("### 👤 Verificação de Convidado")
        
        name_input = st.text_input("Digite seu nome completo e acione o botão 'Verificar':", 
                                   placeholder="Ex: João da Silva")
        
        if st.button("Verificar"):
            if name_input:
                participant = find_participant(name_input, participants_df)
                
                if participant is not None:
                    st.session_state.participant_data = participant
                    st.success(f"✅ Olá, {participant['full_name']}!")
                    st.session_state.confirmed = True
                    st.rerun()
                else:
                    st.error(MESSAGES['not_found'])
            else:
                st.warning("Por favor, digite seu nome.")

def admin_panel():
    """Admin panel for viewing reservations."""
    st.title("🔐 Painel Administrativo - Reservas de Hotel")
    
    password = st.text_input("Senha:", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("Acesso autorizado!")
        
        # Load reservations
        try:
            df = pd.read_csv('./data/RESERVAS.CSV')
            
            # Statistics
            st.markdown("### 📊 Estatísticas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Reservas", len(df))
            
            with col2:
                total_revenue = df['total_amount'].sum()
                st.metric("Valor Total", f"R$ {total_revenue:.2f}")
            
            with col3:
                avg_amount = df['total_amount'].mean()
                st.metric("Ticket Médio", f"R$ {avg_amount:.2f}")
            
            # Reservations table
            st.markdown("### 📋 Lista de Reservas")
            st.dataframe(df.sort_values('timestamp', ascending=False))
            
            # Export option
            if FEATURES['export_data']:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name=f"reservas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        except FileNotFoundError:
            st.info("Nenhuma reserva registrada ainda.")
    
    elif password:
        st.error("Senha incorreta!")

# Run the app
if __name__ == "__main__":
    # Check if admin mode
    query_params = st.query_params
    
    if 'admin' in query_params:
        admin_panel()
    else:
        main()