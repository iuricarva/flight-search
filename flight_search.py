import time
import schedule
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import random
import requests
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
ORIGINS = os.getenv('ORIGINS', 'CNF,GIG').split(',')
DESTINATIONS = os.getenv('DESTINATIONS', 'LIS,OPO,DUB,ZRH,AMS,MAD').split(',')
START_DATE = datetime.strptime(os.getenv('TRIP_START', '2026-09-05'), '%Y-%m-%d')
END_DATE = datetime.strptime(os.getenv('TRIP_END', '2026-09-25'), '%Y-%m-%d')
MAX_PRICE = float(os.getenv('MAX_PRICE_BRL', '6500'))

# Email
EMAIL_FROM = os.getenv('EMAIL_FROM', 'seu_email@gmail.com')
EMAIL_TO = os.getenv('EMAIL_TO', 'seu_email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Ollama LLM
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')

# Stopover routes (conexões intermediárias para melhor preço)
STOPOVER_ROUTES = [
    {'origin': 'CNF', 'stopover': 'LIS', 'destination': 'DUB'},
    {'origin': 'GIG', 'stopover': 'LIS', 'destination': 'DUB'},
]

# Multi-stopover routes (rotas complexas com múltiplos destinos)
MULTI_STOPOVER_ROUTES = [
    {
        'segments': [
            {'from': 'CNF', 'to': 'LIS', 'date': '2026-09-05', 'stopover_days': 6},
            {'from': 'LIS', 'to': 'DUB', 'date': '2026-09-12', 'stopover_days': None},
        ],
        'return_date': '2026-09-25'
    },
    {
        'segments': [
            {'from': 'GIG', 'to': 'LIS', 'date': '2026-09-05', 'stopover_days': 4},
            {'from': 'LIS', 'to': 'ZRH', 'date': '2026-09-10', 'stopover_days': None},
        ],
        'return_date': '2026-09-25'
    },
    {
        'segments': [
            {'from': 'CNF', 'to': 'MAD', 'date': '2026-09-05', 'stopover_days': 5},
            {'from': 'MAD', 'to': 'AMS', 'date': '2026-09-11', 'stopover_days': None},
        ],
        'return_date': '2026-09-25'
    },
]

def consult_ollama(prompt):
    """Consultar Ollama LLM para análise de dados de voos"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        response = requests.post(url, json=payload, timeout=120)  # Aumentado para 120s
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            print(f"⚠️ Ollama retornou: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"⚠️ Ollama timeout (Mistral é lento na primeira requisição, tente novamente)")
        return None
    except Exception as e:
        print(f"⚠️ Ollama offline: {e}")
        return None

def search_flights(origin, destination, date):
    """Buscar voos diretos entre origem e destino"""
    print(f"  Pesquisando voos: {origin} → {destination} em {date.strftime('%Y-%m-%d')}")
    time.sleep(0.5)
    
    # Mapeamento de links de compra por companhia
    booking_links = {
        'TAP': 'https://www.tap.pt',
        'LATAM': 'https://www.latam.com/pt_BR/',
        'Air Europa': 'https://www.aireuropa.com',
        'RyanAir': 'https://www.ryanair.com'
    }
    
    # Simular voos com preços e horários realistas
    mock_flights = [
        {
            'price': random.randint(4500, 5800),
            'outbound_departure': '08:30',
            'outbound_arrival': '20:45',
            'return_departure': '10:15',
            'return_arrival': '06:30',
            'duration': '10h 30m',
            'stops': 1,
            'layover_location': 'Madrid (MAD)',
            'layover_duration': '2h 15m',
            'source': 'Skyscanner',
            'airlines': 'TAP'
        },
        {
            'price': random.randint(4000, 5500),
            'outbound_departure': '14:20',
            'outbound_arrival': '02:35',
            'return_departure': '18:50',
            'return_arrival': '12:10',
            'duration': '12h 15m',
            'stops': 0,
            'layover_location': None,
            'layover_duration': None,
            'source': 'Skyscanner',
            'airlines': 'LATAM'
        },
    ]
    
    flights = []
    for flight in mock_flights:
        if flight['stops'] <= 2 and flight['price'] <= MAX_PRICE:
            flights.append({
                'origin': origin,
                'stopover': None,
                'stopover_hours': None,
                'destination': destination,
                'departure_date': date.strftime('%Y-%m-%d'),
                'return_date': (date + timedelta(days=20)).strftime('%Y-%m-%d'),
                'outbound_departure': flight['outbound_departure'],
                'outbound_arrival': flight['outbound_arrival'],
                'return_departure': flight['return_departure'],
                'return_arrival': flight['return_arrival'],
                'price': flight['price'],
                'duration': flight['duration'],
                'stops': flight['stops'],
                'layover_location': flight['layover_location'],
                'layover_duration': flight['layover_duration'],
                'source': flight['source'],
                'airlines': flight['airlines'],
                'route_type': 'direto',
                'booking_url': booking_links.get(flight['airlines'], 'https://www.skyscanner.com')
            })
    return flights

def search_stopover_flights(origin, stopover, destination, date):
    """Buscar voos com stopover (conexão intermediária)"""
    print(f"  Pesquisando stopover: {origin} → {stopover} → {destination} em {date.strftime('%Y-%m-%d')}")
    time.sleep(0.5)
    
    booking_links = {
        'Air Europa': 'https://www.aireuropa.com',
        'RyanAir': 'https://www.ryanair.com'
    }
    
    # Simular voos com stopover - com horários reais
    mock_flights = [
        {
            'price': random.randint(3800, 5200),
            'outbound_dep_origin': '09:00',
            'outbound_arr_stopover': '18:30',
            'outbound_dep_stopover': '20:45',
            'outbound_arr_dest': '23:15',
            'return_dep_dest': '15:30',
            'return_arr_stopover': '18:00',
            'return_dep_stopover': '06:00',
            'return_arr_origin': '14:30',
            'duration': '18h 00m',
            'stops': 1,
            'stopover_hours': '3-7',
            'airlines': 'Air Europa'
        },
        {
            'price': random.randint(3500, 4900),
            'outbound_dep_origin': '16:20',
            'outbound_arr_stopover': '23:50',
            'outbound_dep_stopover': '07:15',
            'outbound_arr_dest': '09:45',
            'return_dep_dest': '21:00',
            'return_arr_stopover': '23:30',
            'return_dep_stopover': '13:00',
            'return_arr_origin': '19:00',
            'duration': '20h 30m',
            'stops': 1,
            'stopover_hours': '6-12',
            'airlines': 'RyanAir'
        },
    ]
    
    flights = []
    for flight in mock_flights:
        if flight['stops'] <= 2 and flight['price'] <= MAX_PRICE:
            flights.append({
                'origin': origin,
                'stopover': stopover,
                'stopover_hours': flight['stopover_hours'],
                'destination': destination,
                'departure_date': date.strftime('%Y-%m-%d'),
                'return_date': (date + timedelta(days=20)).strftime('%Y-%m-%d'),
                'outbound_departure': flight['outbound_dep_origin'],
                'outbound_stopover_arrival': flight['outbound_arr_stopover'],
                'outbound_stopover_departure': flight['outbound_dep_stopover'],
                'outbound_arrival': flight['outbound_arr_dest'],
                'return_departure': flight['return_dep_dest'],
                'return_stopover_arrival': flight['return_arr_stopover'],
                'return_stopover_departure': flight['return_dep_stopover'],
                'return_arrival': flight['return_arr_origin'],
                'price': flight['price'],
                'duration': flight['duration'],
                'stops': flight['stops'],
                'layover_location': stopover,
                'source': 'Skyscanner',
                'airlines': flight['airlines'],
                'route_type': f"stopover em {stopover}",
                'booking_url': booking_links.get(flight['airlines'], 'https://www.skyscanner.com')
            })
    return flights

def search_tap_flights(origin, destination, departure_date, return_date):
    """Pesquisar voos na TAP Air Portugal"""
    print(f"  Pesquisando TAP: {origin} → {destination}")
    time.sleep(0.5)
    
    mock_tap_flights = [
        {
            'price': random.randint(4800, 6200),
            'outbound_departure': '11:00',
            'outbound_arrival': '22:45',
            'return_departure': '09:30',
            'return_arrival': '05:15',
            'duration': '11h 45m',
            'stops': 1,
            'layover_location': 'Porto (OPO)',
            'layover_duration': '1h 30m',
            'airlines': 'TAP'
        },
        {
            'price': random.randint(5200, 6500),
            'outbound_departure': '07:15',
            'outbound_arrival': '16:45',
            'return_departure': '19:00',
            'return_arrival': '14:30',
            'duration': '9h 30m',
            'stops': 0,
            'layover_location': None,
            'layover_duration': None,
            'airlines': 'TAP'
        },
    ]
    
    flights = []
    for flight in mock_tap_flights:
        if flight['stops'] <= 2 and flight['price'] <= MAX_PRICE:
            flights.append({
                'origin': origin,
                'stopover': None,
                'stopover_hours': None,
                'destination': destination,
                'departure_date': departure_date.strftime('%Y-%m-%d'),
                'return_date': return_date.strftime('%Y-%m-%d'),
                'outbound_departure': flight['outbound_departure'],
                'outbound_arrival': flight['outbound_arrival'],
                'return_departure': flight['return_departure'],
                'return_arrival': flight['return_arrival'],
                'price': flight['price'],
                'duration': flight['duration'],
                'stops': flight['stops'],
                'layover_location': flight['layover_location'],
                'layover_duration': flight['layover_duration'],
                'source': 'TAP Air Portugal',
                'airlines': flight['airlines'],
                'route_type': 'direto',
                'booking_url': 'https://www.tap.pt'
            })
    return flights

def search_multi_stopover_flights(route_config):
    """Buscar voos com múltiplos stopovers (rotas complexas)"""
    segments = route_config['segments']
    return_date = route_config['return_date']
    
    print(f"  Pesquisando rota multi-stopover: {segments[0]['from']} → {' → '.join([s['to'] for s in segments])}")
    time.sleep(0.5)
    
    # Simular voos com múltiplos segmentos
    mock_multi_flights = [
        {
            'price': random.randint(4200, 5800),
            'segments': [
                {
                    'departure': '08:30',
                    'arrival': '20:45',
                    'duration': '10h 30m',
                    'stops': 1,
                    'layover_location': 'Madrid (MAD)',
                    'layover_duration': '2h 15m',
                    'airlines': 'TAP'
                },
                {
                    'departure': '14:20',
                    'arrival': '16:35',
                    'duration': '2h 15m',
                    'stops': 0,
                    'layover_location': None,
                    'layover_duration': None,
                    'airlines': 'RyanAir'
                }
            ],
            'return_departure': '10:15',
            'return_arrival': '06:30',
            'return_duration': '20h 15m',
            'total_duration': '33h 00m'
        },
        {
            'price': random.randint(4500, 6000),
            'segments': [
                {
                    'departure': '11:00',
                    'arrival': '22:30',
                    'duration': '9h 30m',
                    'stops': 0,
                    'layover_location': None,
                    'layover_duration': None,
                    'airlines': 'LATAM'
                },
                {
                    'departure': '07:15',
                    'arrival': '09:45',
                    'duration': '2h 30m',
                    'stops': 0,
                    'layover_location': None,
                    'layover_duration': None,
                    'airlines': 'Air Europa'
                }
            ],
            'return_departure': '18:50',
            'return_arrival': '14:10',
            'return_duration': '19h 20m',
            'total_duration': '31h 20m'
        },
    ]
    
    flights = []
    for flight in mock_multi_flights:
        if flight['price'] <= MAX_PRICE:
            # Construir booking_url simulado para Skyscanner multi-city
            legs = []
            for i, segment in enumerate(segments):
                legs.append(f"{segment['from']}/{segment['to']}/{segment['date'].replace('-', '')}")
            legs_str = '/'.join(legs)
            booking_url = f"https://www.skyscanner.com/transport/flights/{legs_str}/?adultsv2=1&cabinclass=economy&childrenv2=&inboundaltsenabled=false&infantsv2=&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=1"
            
            flights.append({
                'origin': segments[0]['from'],
                'stopover': ', '.join([str(s['to']) for s in segments[:-1]]),
                'stopover_hours': ', '.join([f"{s['stopover_days']} dias" for s in segments if s['stopover_days']]),
                'destination': segments[-1]['to'],
                'departure_date': segments[0]['date'],
                'return_date': return_date,
                'outbound_departure': flight['segments'][0]['departure'],
                'outbound_arrival': flight['segments'][-1]['arrival'],
                'return_departure': flight['return_departure'],
                'return_arrival': flight['return_arrival'],
                'price': flight['price'],
                'duration': flight['total_duration'],
                'stops': sum(s['stops'] for s in flight['segments']),
                'layover_location': ', '.join([str(s['layover_location']) for s in flight['segments'] if s['layover_location']]),
                'layover_duration': ', '.join([str(s['layover_duration']) for s in flight['segments'] if s['layover_duration']]),
                'source': 'Skyscanner',
                'airlines': ', '.join(set([str(s['airlines']) for s in flight['segments']])),
                'route_type': f"multi-stopover ({len(segments)} trechos)",
                'booking_url': booking_url,
                'route_segments': segments,  # Adicionar os segmentos da rota
                'flight_segments': flight['segments']  # Detalhes dos voos
            })
    return flights

def rank_flights(flights_list):
    """Ranquear voos por menor preço e criar dataframe"""
    if not flights_list:
        return None
    
    df = pd.DataFrame(flights_list)
    df = df.sort_values('price')
    df = df.reset_index(drop=True)
    df['ranking'] = range(1, len(df) + 1)
    return df

def get_ollama_analysis(flights_df):
    """Obter análise do Ollama sobre melhores opções"""
    if flights_df is None or len(flights_df) == 0:
        return "Nenhum voo disponível para análise."
    
    top_3 = flights_df.head(3).to_dict('records')
    
    prompt = f"""Analise estas 3 melhores opções de voo para viagem Brasil → Europa (ordenadas por preço):
    
{json.dumps(top_3, indent=2, ensure_ascii=False, default=str)}
    
Forneça uma análise breve (máx 3 linhas) em português destacando qual é a MELHOR opção considerando preço, duração, conveniência e se vale a pena fazer stopover."""
    
    print("\n🤖 Consultando Ollama para análise inteligente...")
    analysis = consult_ollama(prompt)
    
    if analysis:
        return analysis.strip()
    return "Análise indisponível (Ollama offline)"

def format_email_html(flights_df, analysis):
    """Formatar email com HTML contendo tabela de voos ranqueados com horários e links"""
    
    if flights_df is None or len(flights_df) == 0:
        return "<h3>Nenhum voo encontrado dentro do orçamento.</h3>"
    
    # Pegar top 10 voos
    top_flights = flights_df.head(10)
    
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Arial', sans-serif; color: #333; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
            h1 {{ color: #0066cc; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
            h2 {{ color: #0066cc; margin-top: 30px; }}
            h3 {{ color: #666; }}
            .flight-card {{ border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 6px; background-color: #fafafa; }}
            .flight-card.best {{ background-color: #e8f5e9 !important; border-left: 4px solid #4CAF50; }}
            .flight-header {{ font-size: 1.2em; font-weight: bold; color: #0066cc; margin-bottom: 10px; }}
            .flight-details {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
            .detail-section {{ background: white; padding: 12px; border-radius: 4px; border-left: 3px solid #0066cc; }}
            .detail-section h4 {{ margin: 0 0 8px 0; color: #ff6f00; font-size: 0.9em; text-transform: uppercase; }}
            .time-info {{ font-size: 1.1em; font-weight: bold; color: #333; }}
            .time-label {{ font-size: 0.8em; color: #666; }}
            .layer-info {{ background-color: #fff3cd; padding: 8px; margin-top: 5px; border-radius: 3px; font-size: 0.85em; }}
            .stopover-info {{ background-color: #e3f2fd; padding: 10px; margin-top: 10px; border-left: 3px solid #2196F3; border-radius: 3px; }}
            .stopover-info strong {{ color: #1976D2; }}
            .price-box {{ background-color: #c8e6c9; padding: 10px; border-radius: 4px; text-align: center; }}
            .price {{ font-size: 1.3em; font-weight: bold; color: #28a745; }}
            .booking-btn {{ background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; font-weight: bold; }}
            .booking-btn:hover {{ background-color: #0052a3; }}
            .analysis {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 4px; }}
            .analysis h3 {{ color: #ff6f00; margin-top: 0; }}
            .info-box {{ background-color: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 4px; border-left: 4px solid #0066cc; }}
            .footer {{ color: #999; margin-top: 40px; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px; text-align: center; }}
            .ranking {{ font-size: 1.8em; font-weight: bold; color: #0066cc; }}
            .badge-container {{ margin: 10px 0; }}
            .badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-size: 0.85em; font-weight: bold; margin-right: 5px; }}
            .direct-badge {{ background-color: #4CAF50; color: white; }}
            .stopover-badge {{ background-color: #ff9800; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✈️ Alerta de Melhores Preços de Passagens Aéreas</h1>
            <p><strong>Data da busca:</strong> {}</p>
            <p><strong>Período de viagem:</strong> {} até {}</p>
            
            <div class="analysis">
                <h3>🤖 Análise Inteligente (Ollama):</h3>
                <p>{}</p>
            </div>
            
            <div class="info-box">
                <strong>ℹ️ Dica:</strong> Voos com <span class="badge stopover-badge">Stopover</span> geralmente oferecem melhor preço! 
                Uma conexão estratégica em Lisboa pode economizar centenas de reais.
            </div>
            
            <h2>🏆 Top 10 Melhores Opções Detalhadas:</h2>
    """.format(
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        top_flights.iloc[0]['departure_date'] if len(top_flights) > 0 else '',
        top_flights.iloc[0]['return_date'] if len(top_flights) > 0 else '',
        analysis
    )
    
    for idx, row in top_flights.iterrows():
        rank = int(row['ranking'])
        origin = str(row['origin'])
        stopover_val = row['stopover'] if pd.notna(row['stopover']) else None
        # Converter para string e verificar se não é 'nan'
        stopover_str = str(stopover_val) if stopover_val is not None else ''
        is_stopover = stopover_val is not None and stopover_str.lower() != 'nan' and stopover_str != ''
        
        stopover_info = f" → {stopover_str}" if is_stopover else ""
        destination = str(row['destination'])
        route = f"{origin}{stopover_info} → {destination}"
        airline = str(row['airlines']) if pd.notna(row['airlines']) else 'N/A'
        price = float(row['price'])
        
        # Acessar booking_url de forma segura
        try:
            booking_url = row['booking_url'] if pd.notna(row['booking_url']) else 'https://www.skyscanner.com'
        except KeyError:
            booking_url = 'https://www.skyscanner.com'
        
        css_class = 'best' if rank == 1 else ''
        medal = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][idx] if idx < 10 else '•'
        
        badge_type = 'stopover-badge' if is_stopover else 'direct-badge'
        badge_text = 'Com Stopover' if is_stopover else 'Voo Direto'
        
        # Construir seção de ida
        has_route_segments = False
        try:
            route_segments_val = row['route_segments']
            has_route_segments = (('route_segments' in row.index) and 
                                 pd.notna(route_segments_val) and 
                                 isinstance(route_segments_val, list) and
                                 len(route_segments_val) > 0)
        except (KeyError, TypeError, ValueError):
            has_route_segments = False
        
        if has_route_segments:
            # Multi-stopover: mostrar todos os segmentos
            route_segments = row['route_segments']
            flight_segments = row['flight_segments']
            ida_section = f"""
        <div class="detail-section">
            <h4>✈️ Ida (Múltiplos Trechos)</h4>"""
            for i, (seg, fseg) in enumerate(zip(route_segments, flight_segments)):
                ida_section += f"""
            <div class="time-info">Trecho {i+1}: {seg['from']} → {seg['to']}</div>
            <div class="time-label">{seg['date']} | {fseg['departure']} - {fseg['arrival']} | {fseg['airlines']}</div>
            <div class="layer-info">Duração: {fseg['duration']} | Escalas: {fseg['stops']}</div>"""
                if fseg['layover_location']:
                    ida_section += f"<div class='layer-info'>Escala: {fseg['layover_location']} ({fseg['layover_duration']})</div>"
                if seg['stopover_days']:
                    ida_section += f"<div class='stopover-info'>Stopover: {seg['stopover_days']} dias em {seg['to']}</div>"
            ida_section += "</div>"
        else:
            # Ida normal (direto ou stopover simples)
            ida_section = f"""
        <div class="detail-section">
            <h4>{'✈️ Ida' if not is_stopover else '✈️ Ida (Trechos)'}</h4>
            <div class="time-info">{row.get('outbound_departure', 'N/A')} - {row.get('outbound_arrival', 'N/A')}</div>
            <div class="time-label">{row['departure_date']}</div>
        """
        
        if is_stopover and not has_route_segments:
            ida_section += f"""
            <div class="layer-info">
                <strong>1º Trecho:</strong> {row['origin']} {row.get('outbound_departure', 'N/A')} → {stopover_str} {row.get('outbound_stopover_arrival', 'N/A')}<br>
                <strong>Pausa em {stopover_str}:</strong> {row.get('stopover_hours', 'N/A')} horas<br>
                <strong>2º Trecho:</strong> {stopover_str} {row.get('outbound_stopover_departure', 'N/A')} → {row['destination']} {row.get('outbound_arrival', 'N/A')}
            </div>
            """
        elif pd.notna(row.get('layover_location')) and not has_route_segments:
            layover_loc = row.get('layover_location')
            layover_dur = row.get('layover_duration', 'N/A')
            ida_section += f"""
            <div class="layer-info">
                <strong>Escala:</strong> {layover_loc} ({layover_dur})
            </div>
            """
        
        ida_section += "</div>"
        
        # Construir seção de volta
        volta_section = f"""
        <div class="detail-section">
            <h4>🔄 Volta (Retorno)</h4>
            <div class="time-info">{row.get('return_departure', 'N/A')} - {row.get('return_arrival', 'N/A')}</div>
            <div class="time-label">{row['return_date']}</div>
        """
        
        if is_stopover and str(stopover_val).lower() != 'nan' and not has_route_segments:
            volta_section += f"""
            <div class="layer-info">
                <strong>1º Trecho:</strong> {row['destination']} {row.get('return_departure', 'N/A')} → {stopover_str} {row.get('return_stopover_arrival', 'N/A')}<br>
                <strong>Pausa em {stopover_str}:</strong> {row.get('stopover_hours', 'N/A')} horas<br>
                <strong>2º Trecho:</strong> {stopover_str} {row.get('return_stopover_departure', 'N/A')} → {row['origin']} {row.get('return_arrival', 'N/A')}
            </div>
            """
        
        volta_section += "</div>"
        
        # Construir seção de preço e link
        price_section = f"""
        <div class="detail-section">
            <h4>💰 Preço & Compra</h4>
            <div class="price-box">
                <div class="price">R$ {price:.2f}</div>
                <div class="time-label">Ida + Volta</div>
            </div>
            <a href="{booking_url}" target="_blank" class="booking-btn">🔗 Comprar Passagem</a>
        </div>
        """
        
        # Construir stopover info se houver
        stopover_section = ""
        if has_route_segments:
            # Para multi-stopover, mostrar stopovers dos segmentos
            route_segments = row['route_segments']
            stopovers = [s for s in route_segments if s['stopover_days']]
            if stopovers:
                stopover_section = f"""
            <div class="stopover-info">
                <strong>💡 Sugestões de Stopover:</strong><br>"""
                for s in stopovers:
                    stopover_section += f"• {s['stopover_days']} dias em {s['to']} (ideal para exploração)<br>"
                stopover_section += "</div>"
        elif is_stopover and stopover_str.lower() != 'nan':
            stopover_section = f"""
            <div class="stopover-info">
                <strong>💡 Sugestão de Stopover em {stopover_str}:</strong><br>
                Período recomendado: <strong>{row.get('stopover_hours', '3-5')} horas</strong><br>
                Ideal para descanso, refeição rápida e exploração local durante a pausa.
            </div>
            """
        
        html += f"""
        <div class="flight-card {css_class}">
            <div class="flight-header">{medal} #{rank} - {route}</div>
            <div class="badge-container">
                <span class="badge {badge_type}">{badge_text}</span>
                <span class="badge" style="background-color: #673AB7; color: white;">{airline}</span>
                <span class="badge" style="background-color: #009688; color: white;">Duração: {row['duration']}</span>
            </div>
            <div class="flight-details">
                {ida_section}
                {volta_section}
                {price_section}
            </div>
            {stopover_section}
        </div>
        """
    
    html += """
            <h2>📊 Resumo da Busca</h2>
            <ul>
                <li><strong>Orçamento máximo:</strong> R$ {:.2f}</li>
                <li><strong>Total de voos analisados:</strong> {}</li>
                <li><strong>Melhor preço encontrado:</strong> R$ {:.2f} (economia de R$ {:.2f} vs orçamento)</li>
                <li><strong>Período de viagem:</strong> 20 dias</li>
                <li><strong>Filtro de conforto:</strong> Máximo 2 escalas, duração ≤36h</li>
                <li><strong>Classe:</strong> Econômica com bagagem de mão</li>
            </ul>
            
            <div class="footer">
                <p>Este é um alerta automático gerado pela rotina inteligente de busca de passagens aéreas.<br>
                <strong>Última atualização:</strong> {}</p>
                <p style="font-size: 0.85em; color: #bbb;">Powered by Ollama LLM + Python Script</p>
                <p style="font-size: 0.8em; color: #ccc;">Os links de compra levam aos sites oficiais das companhias. Preços podem variar.</p>
            </div>
        </div>
    </body>
    </html>
    """.format(
        MAX_PRICE,
        len(flights_df),
        flights_df.iloc[0]['price'],
        MAX_PRICE - flights_df.iloc[0]['price'],
        datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
    )
    
    return html

def send_email(flights_df, analysis):
    """Enviar alerta por email com HTML e tabela de voos ranqueados"""
    try:
        html_content = format_email_html(flights_df, analysis)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✈️ Alerta: Melhores Preços de Passagens (R${flights_df.iloc[0]["price"]:.2f})'
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        # Versão plain text
        text_part = MIMEText("Verifique seu email em HTML para ver a tabela de voos.", 'plain')
        msg.attach(text_part)
        
        # Versão HTML
        html_part = MIMEText(html_content, 'html', _charset='utf-8')
        msg.attach(html_part)

        print("📧 Enviando email com tabela HTML elegante...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        print(f"✓ Email enviado com sucesso para {EMAIL_TO}!")
        
    except Exception as e:
        import traceback
        print(f"✗ Erro ao enviar email: {e}")
        traceback.print_exc()

def find_best_flights():
    """Buscar e ranquear melhores voos com análise Ollama"""
    print("\n" + "="*80)
    print("🔍 INICIANDO BUSCA DE PASSAGENS AÉREAS (com análise Ollama)")
    print("="*80)
    
    all_flights = []
    departure_date = START_DATE
    return_date = END_DATE
    
    # Buscar voos diretos
    print("\n📍 Buscando voos diretos...")
    for origin in ['CNF']:  # Foco em Belo Horizonte
        for dest in ['LIS', 'OPO', 'DUB']:
            flights = search_flights(origin, dest, departure_date)
            all_flights.extend(flights)
    
    # Buscar com TAP
    print("\n🎫 Buscando voos TAP Air Portugal...")
    for origin in ['CNF']:
        for dest in ['LIS', 'DUB']:
            tap_flights = search_tap_flights(origin, dest, departure_date, return_date)
            all_flights.extend(tap_flights)
    
    # Buscar com stopovers (conexões estratégicas)
    print("\n✈️ Buscando rotas com Stopover (conexões intermediárias)...")
    for route in STOPOVER_ROUTES:
        stopover_flights = search_stopover_flights(
            route['origin'], 
            route['stopover'], 
            route['destination'],
            departure_date
        )
        all_flights.extend(stopover_flights)
    
    # Buscar rotas multi-stopover (múltiplos destinos)
    print("\n🌍 Buscando rotas Multi-Stopover (viagens complexas)...")
    for route_config in MULTI_STOPOVER_ROUTES:
        multi_flights = search_multi_stopover_flights(route_config)
        all_flights.extend(multi_flights)
    
    # Ranquear voos por menor preço
    print("\n📊 Ranqueando {} voos por melhor preço...".format(len(all_flights)))
    flights_df = rank_flights(all_flights)
    
    print(f"✅ Total de voos encontrados: {len(flights_df) if flights_df is not None else 0}")
    
    if flights_df is not None and len(flights_df) > 0:
        # Exibir top 5 no console
        print("\n" + "="*80)
        print("🏆 TOP 5 MELHORES OPÇÕES (RANQUEADAS):")
        print("="*80)
        for idx, row in flights_df.head(5).iterrows():
            stopover_val = row['stopover'] if pd.notna(row['stopover']) else None
            stopover_info = f" → {stopover_val}" if (stopover_val and str(stopover_val).lower() != 'nan') else ""
            medal = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][idx]
            print(f"{medal} Ranking {row['ranking']}: {row['origin']}{stopover_info} → {row['destination']} | "
                  f"R${row['price']:.2f} | {row['airlines']} | {row['duration']} | {row['route_type']}")
        
        # Consultar Ollama para análise
        analysis = get_ollama_analysis(flights_df)
        print(f"\n{analysis}\n")
        
        # Enviar email com HTML
        send_email(flights_df, analysis)
    else:
        print("❌ Nenhum voo encontrado dentro do orçamento.")

# Agendamento diário
schedule.every().day.at("09:00").do(find_best_flights)

if __name__ == "__main__":
    find_best_flights()  # Executar uma vez
    
    print("\n" + "="*80)
    print("⏰ SISTEMA DE AGENDAMENTO ATIVO")
    print("="*80)
    print("Próxima execução: 09:00 de amanhã")
    print("Script rodando em background...\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)