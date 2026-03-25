# 🌍 Guia: Integração com APIs Reais de Busca de Passagens Aéreas

## ⚠️ Status Atual
O script está usando **dados simulados (MOCK)** para testes. Para buscar **valores reais de passagens**, você precisa integrar com APIs reais de agências de viagem ou plataformas de busca aérea.

---

## 🏆 Melhores Opções de APIs Reais

### 1️⃣ **Google Flights API** (Recomendado)
**Características:**
- ✅ Dados reais atualizados
- ✅ Visa e viabilidade de passagens
- ✅ Integração com múltiplas companhias aéreas
- ⚠️ Requer Google Cloud Console
- ⚠️ Pode ter custos

**Como usar:**
```bash
# 1. Criar projeto no Google Cloud Console
# https://console.cloud.google.com/

# 2. Ativar Flight Search API
# 3. Gerar credenciais (Service Account)
# 4. Instalar biblioteca
pip install google-flights-api
```

**Exemplo de código:**
```python
from google.auth import default
from google_flights_api import FlightsClient

credentials, project_id = default()
client = FlightsClient(credentials=credentials, project_id=project_id)

# Buscar voos
response = client.search_flights(
    origin='CNF',  # Rio de Janeiro
    destination='LIS',  # Lisboa
    date='2026-09-05',
    return_date='2026-09-25',
    adults=1,
    currency='BRL'
)

for flight in response.flights:
    print(f"{flight.airline} - R$ {flight.price}")
```

---

### 2️⃣ **Skyscanner API** (Alternativa Popular)
**Características:**
- ✅ API bem documentada
- ✅ Muitas opções de filtros
- ✅ Suporta múltiplas moedas
- ⚠️ Requer API Key paga
- ⚠️ Rate limiting

**Como usar:**
```bash
# 1. Criar conta em https://www.skyscanner.com/
# 2. Registrar app em https://partners.skyscanner.com/

# 3. Instalar biblioteca
pip install skyscanner
```

**Exemplo de código:**
```python
from skyscanner.skyscanner import Skyscanner

skyscanner = Skyscanner('BRL', 'PT')

# Buscar voos diretos
response = skyscanner.flights.search(
    originplace='CNF-sky',  # Belo Horizonte
    destinationplace='LIS-sky',  # Lisboa
    outbounddate='2026-09-05',
    inbounddate='2026-09-25',
    adults=1
)

for itinerary in response['Itineraries']:
    price = itinerary['PricingOptions'][0]['Price']
    print(f"R$ {price}")
```

---

### 3️⃣ **Amadeus API** (Profissional)
**Características:**
- ✅ Dados em tempo real de agências
- ✅ Integração com múltiplas companhias
- ✅ Suporte a booking
- ⚠️ Requer credenciais comerciais
- ⚠️ Custo mensal

**Como usar:**
```bash
# 1. Registrar em https://developer.amadeus.com/
# 2. Criar app e obter API Key
# 3. Instalar biblioteca
pip install amadeus
```

**Exemplo de código:**
```python
from amadeus import Client

amadeus = Client(
    client_id='SUA_API_KEY',
    client_secret='SUA_SECRET'
)

# Buscar voos com preços
response = amadeus.shopping.flight_offers_search.get(
    originLocationCode='CNF',
    destinationLocationCode='LIS',
    departureDate='2026-09-05',
    returnDate='2026-09-25',
    adults=1,
    currencyCode='BRL'
)

for flight in response.data:
    price = flight['price']['total']
    print(f"R$ {price}")
```

---

### 4️⃣ **Kiwi.com API** (Para Rotas com Stopover)
**Características:**
- ✅ Especializada em rotas com stopover
- ✅ Excelente para tours multi-cidades
- ✅ Preços competitivos
- ⚠️ Requer API Key gratuita

**Como usar:**
```bash
# 1. Registrar em https://tequila.kiwi.com/
# 2. Obter API Key (gratuito)
# 3. Instalar biblioteca
pip install kiwi-tequila
```

**Exemplo de código:**
```python
import requests

API_KEY = 'SUA_API_KEY'
ENDPOINT = 'https://tequila-api.kiwi.com/v2/search'

params = {
    'fly_from': 'CNF',  # Origem
    'fly_to': 'LIS',    # Destino
    'dateFrom': '05Sep2026',
    'dateTo': '25Sep2026',
    'layover': '5-7h',  # Stopover 5-7 horas
    'curr': 'BRL',
    'adults': '1'
}

response = requests.get(ENDPOINT, params=params, headers={'apikey': API_KEY})
flights = response.json()['data']

for flight in flights:
    print(f"R$ {flight['price']} - {flight['airlines']}")
```

---

### 5️⃣ **Kayak API** (Scraping Alternativo)
**Características:**
- ✅ Agregador de múltiplas fontes
- ✅ Boa cobertura de rotas
- ⚠️ Menos dados em tempo real
- ⚠️ Pode bloquear scraping

```bash
pip install requests beautifulsoup4 selenium
```

---

## 🔄 Como Modificar o Script para APIs Reais

### Passo 1: Instalar Dependências
```bash
# Adicione ao requirements.txt
pip install amadeus
pip install kiwi-tequila
pip install skyscanner
```

### Passo 2: Modificar `search_flights()` para usar API real
```python
def search_flights(origin, destination, date, return_date=None):
    """Buscar voos reais via Amadeus API"""
    if return_date is None:
        return_date = END_DATE
    
    # Remover dados mock e usar API real
    amadeus = Client(
        client_id=os.getenv('AMADEUS_API_KEY'),
        client_secret=os.getenv('AMADEUS_SECRET')
    )
    
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date.strftime('%Y-%m-%d'),
            returnDate=return_date.strftime('%Y-%m-%d'),
            adults=1,
            currencyCode='BRL'
        )
        
        flights = []
        for offer in response.data:
            price = float(offer['price']['total'])
            
            if price <= MAX_PRICE and len(offer['itineraries'][0]['segments']) <= 2:
                flights.append({
                    'origin': origin,
                    'destination': destination,
                    'departure_date': date.strftime('%Y-%m-%d'),
                    'return_date': return_date.strftime('%Y-%m-%d'),
                    'price': price,
                    'airlines': offer['validatingAirlineCodes'][0],
                    'duration': offer['itineraries'][0]['duration'],
                    # ... outros campos
                })
        
        return flights
    except Exception as e:
        print(f"Erro ao buscar voos: {e}")
        return []
```

### Passo 3: Variáveis de Ambiente
```bash
# Adicione ao .env
AMADEUS_API_KEY=sua_chave_aqui
AMADEUS_SECRET=seu_secret_aqui

# Ou para Kiwi
KIWI_API_KEY=sua_chave_aqui
```

---

## 💡 Recomendação Final

Para sua situação específica (Brasil → Europa com stopover 5-7 dias):

### **Melhor Opção: Kiwi.com API**
- ✅ Especializada em rotas com stopover
- ✅ API Key gratuita
- ✅ Preços reais e atualizados
- ✅ Ótima cobertura para Brasil-Europa

### **Implementação Gradual:**
1. **Fase 1**: Manter mock para testes
2. **Fase 2**: Integrar Kiwi.com API para stopovers
3. **Fase 3**: Adicionar Amadeus para voos diretos
4. **Fase 4**: Implementar cache para economizar requisições

---

## ⚠️ Próximos Passos

1. Escolha a API (recomendo Kiwi.com)
2. Registre e obtenha credenciais
3. Modifique as funções `search_flights()`, `search_stopover_flights()`, etc.
4. Teste com um pré-requisito de dados reais
5. Implemente tratamento de erros robusto
6. Adicione cache para evitar requisições duplicadas

---

## 🔗 Referências Úteis

- [Amadeus Developers](https://developers.amadeus.com/)
- [Skyscanner Partners](https://partners.skyscanner.com/)
- [Kiwi Tequila API](https://tequila.kiwi.com/)
- [Google Flights API](https://cloud.google.com/solutions/travel-commerce/flights)
- [Kayak API Integration](https://www.kayak.com/partners)

---

## 📝 Notas Importantes

- **Preços**: APIs reais podem ter custos. Kiwi oferece plano gratuito até 50 requisições/dia
- **Rate Limiting**: Implemente fila de requisições para não sobrecarregar as APIs
- **Cache**: Salve resultados por 24h para economizar requisições
- **Testes**: Sempre teste com dados reais antes de colocar em produção
- **Moeda**: Verifique se as APIs retornam preços em BRL ou se precisam conversão

