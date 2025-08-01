"""
Hotel Reservation System - Main Application
A complete web system for managing hotel reservations and payments.
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
    if not isinstance(name, str):
        return ""
    
    name = name.strip()
    if name == "":
        return ""
    
    name = name.lower()
    
    # Normalize to decomposed form and remove accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    
    # Remove non-alphanumeric characters except spaces
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    return name

def string_similarity(str1, str2):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, str1, str2).ratio()

def is_abbreviation(short_name, full_name):
    """Check if short_name is an abbreviation of full_name."""
    short_parts = short_name.split()
    full_parts = full_name.split()
    
    # If short has more parts than full, it can't be an abbreviation
    if len(short_parts) > len(full_parts):
        return False
    
    # Check if all parts of short name exist in full name
    for short_part in short_parts:
        found = False
        for full_part in full_parts:
            if short_part == full_part or full_part.startswith(short_part):
                found = True
                break
        if not found:
            return False
    
    return True

def find_participant_flexible(name, participants_df):
    """Find participant with flexible matching including abbreviations and typos."""
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
            
            # Check if one is abbreviation of the other
            if is_abbreviation(normalized_input, normalized_db_name) or is_abbreviation(normalized_db_name, normalized_input):
                return row
            
            # Check similarity for typos
            similarity = string_similarity(normalized_input, normalized_db_name)
            if similarity > best_score and similarity > 0.85:  # 85% similarity threshold
                best_match = row
                best_score = similarity
    
    if best_match is not None:
        st.success(f"✅ Correspondência encontrada para: {best_match['full_name']}")
        return best_match
    
    st.warning("⚠️ Nenhuma correspondência encontrada na lista de participantes.")
    return None

def load_participants():
    """Load participants from CSV file."""
    try:
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
            st.error("❌ Não foi possível carregar o arquivo de participantes.")
            return pd.DataFrame()
        
        return df
    
    except FileNotFoundError:
        st.error(f"❌ Arquivo não encontrado: {PARTICIPANTS_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo: {str(e)}")
        return pd.DataFrame()

def load_rooms():
    """Load rooms from CSV file."""
    try:
        return pd.read_csv(ROOMS_FILE)
    except Exception as e:
        st.error(f"❌ Erro ao carregar quartos: {str(e)}")
        return pd.DataFrame()

def generate_emv_code(key, amount, merchant_name, city, tx_id=None):
    """Generate 100% valid PIX EMV code following Brazilian Central Bank specs"""
    def format_text(text, max_length, remove_accents=True):
        if remove_accents:
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if not unicodedata.combining(c))
        text = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', text)
        return text[:max_length]
    
    amount_str = f"{amount:.2f}"
    clean_key = re.sub(r'[^a-zA-Z0-9@\.\-]', '', key)
    
    sanitized_merchant = format_text(merchant_name, 25, remove_accents=True).upper()
    sanitized_city = format_text(city, 15, remove_accents=True).upper()
    
    payload = "000201"
    
    # Merchant Account Information
    gui = "BR.GOV.BCB.PIX"
    pix_key_field = f"01{len(clean_key):02d}{clean_key}"
    pix_data = f"0014{gui}{pix_key_field}"
    payload += f"26{len(pix_data):02d}{pix_data}"
    
    mcc = "0000"
    payload += f"52{len(mcc):02d}{mcc}"
    
    currency = "986"
    payload += f"53{len(currency):02d}{currency}"
    
    if amount > 0:
        payload += f"54{len(amount_str):02d}{amount_str}"
    
    country = "BR"
    payload += f"58{len(country):02d}{country}"
    
    payload += f"59{len(sanitized_merchant):02d}{sanitized_merchant}"
    payload += f"60{len(sanitized_city):02d}{sanitized_city}"
    
    if tx_id and tx_id != "***":
        tx_field = f"05{len(tx_id):02d}{tx_id}"
        payload += f"62{len(tx_field):02d}{tx_field}"
    else:
        unique_id = f"PIX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        tx_field = f"05{len(unique_id):02d}{unique_id}"
        payload += f"62{len(tx_field):02d}{tx_field}"
    
    payload += "6304"
    
    crc16 = crcmod.predefined.Crc('crc-ccitt-false')
    crc16.update(payload.encode('utf-8'))
    crc_value = format(crc16.crcValue, '04X')
    
    return payload + crc_value

def generate_pix_qr_code(amount, participant_name, participant_id=None, tx_id=None):
    """Generate PIX QR Code for hotel payment with HH comment"""
    if not tx_id:
        # Add participant ID as comment in transaction ID format: HHNNNHH
        if participant_id is not None and str(participant_id).strip() != '':
            tx_id = f"HH{participant_id}HH"
        else:
            tx_id = f"PIX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    
    pix_payload = generate_emv_code(
        PIX_KEY,
        amount,
        PIX_MERCHANT_NAME,
        PIX_CITY,
        tx_id=tx_id
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(pix_payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format='PNG')
    byte_img = buf.getvalue()
    
    return byte_img, pix_payload

def save_reservation(participant_data, room_selections, total_amount, observations):
    """Save reservation to CSV file."""
    os.makedirs('./data', exist_ok=True)
    
    reservation_id = str(uuid.uuid4())[:8]
    
    reservation_data = {
        'reservation_id': reservation_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'participant_name': participant_data['full_name'],
        'participant_id': participant_data.get('id', ''),
        'total_amount': total_amount,
        'observations': observations,
        'payment_status': 'pending'
    }
    
    # Add room selections
    rooms_df = load_rooms()
    for idx, row in rooms_df.iterrows():
        room_key = f"room_{row['id']}"
        quantity = room_selections.get(room_key, 0)
        reservation_data[f"{row['hotel']}_{row['type']}"] = quantity
    
    file_path = './data/reservas.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = pd.concat([df, pd.DataFrame([reservation_data])], ignore_index=True)
    else:
        df = pd.DataFrame([reservation_data])
    
    df.to_csv(file_path, index=False)
    
    return reservation_id

def show_room_selection():
    """Show room selection interface."""
    participant = st.session_state.participant_data
    
    st.markdown(f"### Bem-vindo(a), {participant['full_name']}! 👋")
    
    # Show lunch participants if any
    if 'participants' in participant and participant['participants'] > 0:
        st.info(f"**Participantes do almoço na Churrascaria Boigalê:** {participant['participants']}")
    
    st.markdown("### 🏨 Seleção de Quartos")
    
    # Room type explanation
    st.markdown("""
    **Tipos de quartos:**
    - **DBL**: Quarto para 2 pessoas com 1 cama de casal ou 2 de solteiro
    - **SGN**: Quarto para 1 pessoa com 1 cama de casal ou 2 de solteiro
    
    **Informações importantes:**
    - Check-In: Sexta-Feira 28NOV2025 14:00
    - Check-Out: Sábado 30NOV2025 14:00
    - Café da manhã incluído
    - Estacionamento não incluído
    - Se precisar de algo diferente, use o campo observações
    """)
    
    st.markdown("---")
    
    # Load and display rooms
    rooms_df = load_rooms()
    if rooms_df.empty:
        st.error("Não foi possível carregar a lista de quartos.")
        return
    
    # Room selection
    total_selected = 0
    selections = {}
    
    for idx, room in rooms_df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{room['hotel']} - {room['type']}**")
        
        with col2:
            st.markdown(f"R$ {room['value']:.2f}")
        
        with col3:
            key = f"room_{room['id']}"
            quantity = st.number_input(
                "Qtd:",
                min_value=0,
                max_value=10,
                value=st.session_state.room_selections.get(key, 0),
                key=key
            )
            selections[key] = quantity
            total_selected += quantity
    
    # Calculate total
    total_amount = 0
    for key, quantity in selections.items():
        if quantity > 0:
            room_id = int(key.split('_')[1])
            room = rooms_df[rooms_df['id'] == room_id].iloc[0]
            total_amount += quantity * room['value']
    
    st.markdown("---")
    st.markdown(f"### 💰 Valor Total: R$ {total_amount:.2f}")
    
    # Proceed button
    if total_selected > 0:
        if st.button("Prosseguir", type="primary"):
            st.session_state.room_selections = selections
            st.session_state.total_amount = total_amount
            st.session_state.show_observations = True
            st.rerun()
    else:
        st.warning("⚠️ Selecione pelo menos 1 quarto para prosseguir.")

def show_observations_form():
    """Show observations form."""
    st.markdown("### 📝 Observações (opcional)")
    
    observations = st.text_area(
        "Digite aqui suas observações ou necessidades especiais:",
        value=st.session_state.observations,
        height=100,
        placeholder="Ex: Preciso de quarto no térreo, berço para bebê, etc."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Voltar", type="secondary"):
            st.session_state.show_observations = False
            st.rerun()
    
    with col2:
        if st.button("Prosseguir para Pagamento", type="primary"):
            st.session_state.observations = observations
            st.session_state.show_payment = True
            st.rerun()

def show_payment_page():
    """Show payment page with QR code."""
    participant = st.session_state.participant_data
    room_selections = st.session_state.room_selections
    total_amount = st.session_state.total_amount
    observations = st.session_state.observations
    
    st.markdown(f"### 💳 Pagamento - {participant['full_name']}")
    st.markdown("---")
    
    # Save reservation
    reservation_id = save_reservation(participant, room_selections, total_amount, observations)
    
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
    
    rooms_df = load_rooms()
    for key, quantity in room_selections.items():
        if quantity > 0:
            room_id = int(key.split('_')[1])
            room = rooms_df[rooms_df['id'] == room_id].iloc[0]
            subtotal = quantity * room['value']
            st.markdown(f"- **{room['hotel']} - {room['type']}:** {quantity} × R$ {room['value']:.2f} = R$ {subtotal:.2f}")
    
    if observations:
        st.markdown(f"**Observações:** {observations}")
    
    st.markdown(f"### 💰 **Total a pagar: R$ {total_amount:.2f}**")
    
    st.markdown("---")
    
    # Payment instructions
    st.markdown(MESSAGES['payment_instructions'])
    
    # Confirmation details
    st.success(f"✅ Reserva registrada! ID: {reservation_id}")
    
    # New reservation button
    if st.button("Nova Reserva", type="primary"):
        st.session_state.confirmed = False
        st.session_state.participant_data = None
        st.session_state.show_payment = False
        st.session_state.show_observations = False
        st.session_state.room_selections = {}
        st.session_state.total_amount = 0
        st.session_state.observations = ""
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
    
    st.markdown(f'<h1 class="event-title">🏨 {EVENT_NAME}</h1>', unsafe_allow_html=True)
    
    st.markdown(f"📅 **Data:** {EVENT_DATE}")
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
        show_observations_form()
    elif not st.session_state.confirmed:
        # Name verification
        st.markdown("### 👤 Verificação de Convidado")
        
        name_input = st.text_input("Digite seu nome completo e acione o botão 'Verificar':", 
                                   placeholder="Ex: João da Silva")
        
        if st.button("Verificar"):
            if name_input:
                participant = find_participant_flexible(name_input, participants_df)
                
                if participant is not None:
                    st.session_state.participant_data = participant
                    st.success(f"✅ Olá, {participant['full_name']}!")
                    st.session_state.confirmed = True
                    st.rerun()
                else:
                    st.error(MESSAGES['not_found'])
            else:
                st.warning("Por favor, digite seu nome.")
    else:
        # Room selection
        show_room_selection()

def admin_panel():
    """Admin panel for viewing reservations."""
    st.title("🔐 Painel Administrativo - Reservas")
    
    password = st.text_input("Senha:", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("Acesso autorizado!")
        
        # Load reservations
        try:
            df = pd.read_csv('./data/reservas.csv')
            
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