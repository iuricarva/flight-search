# 📧 Guia: Como Configurar Email para Alertas de Voos

## Opção 1️⃣: Gmail (Recomendado)

### Passo 1: Ativar Verificação em 2 Fatores
1. Acesse: https://myaccount.google.com/security
2. Clique em "Verificação em 2 etapas" (ou "2-Step Verification")
3. Siga as instruções para ativar (pode ser via SMS ou Google Authenticator)

### Passo 2: Gerar Google App Password
1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione:
   - **App**: Mail
   - **Device**: Windows Computer (ou seu SO)
3. Clique em "Generate"
4. Copie a senha de **16 caracteres** mostrada (sem espaços)

### Passo 3: Configurar .env
```
EMAIL_FROM=seu_email@gmail.com
EMAIL_TO=seu_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Cole aqui (sem espaços)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Passo 4: Testar
```bash
python test_email.py
```

---

## Opção 2️⃣: Yahoo Mail

### Passo 1: Twitter Gerar Senha de App
1. Acesse: https://login.yahoo.com/account/security
2. Clique em "Generate app password"
3. Selecione: Mail > Windows
4. Copie a senha gerada

### Passo 2: Configurar .env
```
EMAIL_FROM=seu_email@yahoo.com
EMAIL_TO=seu_email@yahoo.com
EMAIL_PASSWORD=sua_senha_app
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Passo 3: Testar
```bash
python test_email.py
```

---

## Opção 3️⃣: Outlook/Hotmail

### Passo 1: Configurar .env
```
EMAIL_FROM=seu_email@outlook.com
EMAIL_TO=seu_email@outlook.com
EMAIL_PASSWORD=sua_senha_microsoft
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

### Passo 2: Testar
```bash
python test_email.py
```

---

## Opção 4️⃣: SendGrid (para produção)

Se quiser solução mais robusta:

1. Crie conta em: https://sendgrid.com
2. Gere API Key
3. Configure:
```
EMAIL_FROM=seu_email@seu_dominio.com
SENDGRID_API_KEY=sua_api_key
```

(Requer modificação do script para usar SendGrid SDK)

---

## 🔍 Troubleshooting

### Erro: "Username and Password not accepted" (Gmail)
- ✓ Você gerou **Google App Password** (não a senha da conta)?
- ✓ Copied sem espaços?
- ✓ Verificação em 2 etapas está **ATIVA**?

### Erro: "Connection refused" (Qualquer servidor)
- ✓ Verifique SMTP_SERVER e SMTP_PORT
- ✓ Teste com: `telnet smtp.gmail.com 587`

### Email não chega
- Verifique pasta de spam/lixo
- Aumente timeout: `server.create_message()` pode demorar

---

## ✅ Testar Configuração

Execute:
```bash
python test_email.py
```

Resultado esperado:
```
Testando conexão SMTP...
Servidor: smtp.gmail.com:587
Email: seu_email***
✓ Conexão iniciada com sucesso
✓ Autenticação bem-sucedida!

✓ Testes passaram! Email está configurado corretamente.
```

---

## 🚀 Depois de Configurar

Execute o script de busca:
```bash
python flight_search.py
```

Você receberá alertas automáticos por email com o melhor preço encontrado! 🎉
