# Flight Price Search Automation

Rotina automatizada para busca de preços de passagens aéreas em múltiplas fontes (Skyscanner, TAP Air Portugal, etc.) para viagem à Europa entre 05 e 25 de setembro de 2026. Busca voos com classe econômica, bagagem de mão, máximo 2 escalas e duração total <36h, com orçamento máximo de R$6500.

## Funcionalidades

✅ Busca voos de múltiplas fontes:
- Skyscanner
- TAP Air Portugal
- Extensível para outras companhias

✅ Filtra por condições de conforto:
- Classe econômica
- Máximo 2 escalas
- Duração máxima de voo
- Bagagem de mão

✅ Envia alerta por email com melhor preço encontrado

✅ Executa automaticamente diariamente ou sob demanda

✅ Preços ida e volta em BRL

## Instalação

### 1. Clonar/Baixar o projeto
```bash
cd /home/iuricarva/repo/flight-search
```

### 2. Criar ambiente virtual e instalar dependências
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar arquivo `.env`

Edite o arquivo `.env` com suas credenciais:

```
EMAIL_FROM=seu_email@gmail.com
EMAIL_TO=seu_email_para_receber@gmail.com
EMAIL_PASSWORD=sua_google_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

TRIP_START=2026-09-05
TRIP_END=2026-09-25
MAX_PRICE_BRL=6500

ORIGINS=CNF,GIG
DESTINATIONS=LIS,OPO,DUB,ZRH,AMS,MAD
```

### 4. Gerar Google App Password (para Gmail)

Se você usa Gmail, é necessário gerar uma **Google App Password** em vez de usar a senha da conta:

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Mail" e "Windows Computer" (ou seu sistema)
3. Copie a senha gerada (16 caracteres)
4. Cole no campo `EMAIL_PASSWORD` do arquivo `.env`

**Alternativa para Yahoo ou outros e-mails:**
- Yahoo: https://login.yahoo.com/account/security (gere uma senha de app)
- Outlook/Hotmail: https://account.microsoft.com/security
- Ajuste `SMTP_SERVER` e `SMTP_PORT` conforme necessário

## Uso

### Executar manualmente (teste)
```bash
source .venv/bin/activate
python flight_search.py
```

### Executar com agendamento automático
O script já está configurado para rodar diariamente às 09:00. Para mantê-lo rodando em background:

```bash
nohup python flight_search.py > flight_search.log 2>&1 &
```

Ou use `screen`/`tmux`:
```bash
screen -S flight_search
source .venv/bin/activate
python flight_search.py
# Ctrl+A, depois D para desatachar
```

## Exemplo de Saída

```
Pesquisando voos: CNF -> LIS em 2026-09-05
Pesquisando voos: CNF -> OPO em 2026-09-05
Pesquisando TAP: CNF -> LIS (ida: 2026-09-05, volta: 2026-09-25)
Pesquisando TAP: CNF -> OPO (ida: 2026-09-05, volta: 2026-09-25)

Total de voos encontrados: 8

============================================================
Melhor voo encontrado:
  De: CNF -> Para: OPO
  Data: 2026-09-05
  Preço (ida e volta): R$4280.00
  Duração: 12h 15m
  Escalas: 0
  Fonte: Skyscanner
============================================================

✓ Email enviado com sucesso para seu_email@gmail.com!
```

## Estrutura de Arquivos

```
flight-search/
├── flight_search.py       # Script principal
├── requirements.txt       # Dependências Python
├── .env                   # Configurações (não commitar!)
├── .env.example           # Template de configuração
├── README.md              # Este arquivo
└── .venv/                 # Ambiente virtual
```

## Notas

- O script usa mock/simulação por padrão. Para scraping real, atualize `search_flights()` e `search_tap_flights()` com Selenium.
- Preços em mock variam dentro do orçamento (R$4000-6500).
- Para produção com scraping real:
  - APIs como Amadeus ou Skyscanner são mais confiáveis
  - Implemente retry logic e rate limiting
  - Considere usar proxy para evitar bloqueios
  - TAP: Pode fazer scraping do site ou usar API de parceiros

## Troubleshooting

### Email não envia
- Verifique se usou Google App Password (não a senha da conta)
- Ative "Menos seguro" em https://myaccount.google.com/security se necessário (não recomendado)
- Teste credenciais com: `python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).login(EMAIL, PASS)"`

### Voos não encontrados
- Verifique datas e aeroportos no `.env`
- Ajuste `MAX_PRICE_BRL` se necessário
- Aumente delay em `time.sleep()` se sites estiverem lentos

## Roadmap

- [ ] Integrar com APIs reais (Amadeus, Skyscanner)
- [ ] Adicionar suporte para múltiplos passageiros
- [ ] Implementar análise de tendência com IA
- [ ] Notificações via Telegram/WhatsApp
- [ ] Dashboard web para visualizar histórico