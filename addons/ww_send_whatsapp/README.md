# WW Sale WhatsApp (WAHA Plus) — Odoo 16

Envie cotações/pedidos do **Odoo 16** por **WhatsApp** com **WAHA Plus**, a partir de um botão no `sale.order`.
O módulo gera o PDF (QWeb padrão), abre um **wizard** com mensagem/contato/anexos e envia via **/api/sendFile** (Base64) do WAHA.
Inclui **Configurações** em *Definições → WhatsApp (WAHA Plus)* com **Testar conexão**.

## ✨ Recursos

- Botão **Enviar WhatsApp** no Pedido de Venda (Sales).
- Wizard com:
  - Contato (parceiro/telefone em E.164 ou `chatId@c.us`)
  - Mensagem (texto)
  - Anexos (pré-carrega o PDF principal do pedido)
- Envio de **PDF** em **Base64** para WAHA Plus (`/api/sendFile`).
- **Configurações** (Base URL, API Key, Sessão, Timeout) em `res.config.settings`.
- **Testar conexão** direto das Configurações.
- Registro no *chatter* da ordem e **fechamento do popup** com notificação de sucesso.

---

## 📦 Requisitos

- Odoo **16** (CE ou EE).
- Postgres 14+.
- WAHA Plus em execução (com **sessão** já criada e autenticada).
- Acesso HTTP do Odoo ao WAHA (rede Docker/host).

---

## 🧱 Estrutura

```
ww_sale_whatsapp/
├─ __manifest__.py
├─ models/
│  ├─ __init__.py
│  ├─ sale_order.py
│  ├─ whatsapp_wizard.py
│  └─ res_config_settings.py
├─ views/
│  ├─ sale_order_views.xml
│  ├─ whatsapp_wizard_views.xml
│  └─ res_config_settings_view.xml
├─ security/
│  └─ ir.model.access.csv
└─ data/
   └─ params.xml
```

---

## ⚙️ Configuração (Odoo)

1. **Instale o módulo** `WW Sale WhatsApp (WAHA Plus)`.
2. Vá em **Definições → Configurações → WhatsApp (WAHA Plus)** e preencha:
   - **Base URL**: `http://SEU_IP_OU_HOST:4000`
   - **API Key**: (X-Api-Key do WAHA)
   - **Sessão**: ex. `workwise`
   - **Timeout (s)**: ex. `60`
3. Clique em **Testar conexão**. Você verá uma notificação de sucesso/erro.

> Obs.: O módulo herda da view `base.res_config_settings_view_form` (com *xpath* em `<form>`), o que o torna resiliente a variações de layout.

---

## ▶️ Uso

- Abra um **Pedido de Venda**.
- Clique em **Enviar WhatsApp**.
- No wizard:
  - Informe **Telefone** no formato E.164 (ex.: `5511999999999`) ou `chatId` (ex.: `5511999999999@c.us`).
  - Ajuste a **mensagem**.
  - Confirme os **anexos** (o PDF principal já vem carregado).
  - **Enviar**.
- Odoo:
  - Valida/chatId,
  - Envia `sendFile` (Base64),
  - Registra nota no chatter,
  - Mostra **toast** e **fecha** o popup.

---

## 🔌 WAHA Plus — Endpoints utilizados

### `GET /api/contacts/check-exists`
- Parâmetros: `phone`, `session`
- Cabeçalho: `X-Api-Key: <sua_api_key>`

### `POST /api/sendFile`
- JSON (Base64):
```json
{
  "chatId": "5511999999999@c.us",
  "caption": "Mensagem opcional",
  "file": {
    "mimetype": "application/pdf",
    "filename": "Pedido SO0001.pdf",
    "data": "<BASE64_DO_PDF>"
  },
  "reply_to": null,
  "session": "workwise"
}
```

> O módulo usa **`file.data` (Base64)** por padrão. (Há um parâmetro informativo “Transporte de Arquivo”: `data` ou `url`).

---


## 🔐 Segurança

- **API Key**: armazenada em `ir.config_parameter`; restrinja acesso às Configurações.
- **HTTPS**: proteja o WAHA (Nginx + Let’s Encrypt).
- **Validação de número**: formato E.164 e `check-exists` antes de enviar.
- **Timeouts** configuráveis para evitar travas.
- **Logs**: odoo registra geração de PDF e erros HTTP.

---

## 🛠️ Desenvolvimento

- **Odoo 17**: evite `attrs/states` (removidos); use `groups`, `readonly="1"`, `class` e `colspan`.
- **Fechar popup + notificar**: `display_notification` seguido de `act_window_close`.
- **PDF principal**: `ir.actions.report` QWeb de `sale.order`.
- **Settings**: herdado de `base.res_config_settings_view_form` com `xpath //form`.
- **Arquivos XML**: salve como UTF-8 **sem BOM** e **LF**.

---

## 🧪 Testes rápidos (curl)

**Enviar texto**
```bash
curl -X POST 'http://HOST:4000/api/sendText'   -H 'accept: application/json' -H 'X-Api-Key: SUA_KEY' -H 'Content-Type: application/json'   -d '{
    "chatId": "5511999999999@c.us",
    "text": "Olá! Teste via WAHA",
    "session": "workwise"
  }'
```

**Enviar arquivo (Base64)**
```bash
# gere base64 do PDF
base64 quote.pdf > quote.pdf.b64

# monte o JSON (exemplo)
cat <<'JSON' > payload.json
{
  "chatId": "5511999999999@c.us",
  "caption": "Sua proposta em anexo 🙂",
  "file": {
    "mimetype": "application/pdf",
    "filename": "Pedido_SO0001.pdf",
    "data": "COLAR_AQUI_O_BASE64"
  },
  "reply_to": null,
  "session": "workwise"
}
JSON

# envie
curl -X POST 'http://HOST:4000/api/sendFile'   -H 'accept: application/json' -H 'X-Api-Key: SUA_KEY' -H 'Content-Type: application/json'   --data-binary @payload.json
```

---

## 🗺️ Roadmap

- Templates de mensagem com variáveis (ex.: `{{order.name}}`, `{{amount_total}}`).
- Multi-documentos e imagens (jpg/png) automáticos.
- Histórico WA / status de entrega (quando exposto pela API).
- Suporte a outros modelos (fatura, picking).
- Opção de envio por **URL** (`file.url`) além de Base64.

---

## 🤝 Contribuição

- PRs e issues são bem-vindos.
- Siga o padrão Odoo (pep8, nomes técnicos, i18n com `_()`).

---

## 📄 Licença

LGPL-3 (compatível com Odoo CE).  
© Workwise — adapte conforme sua organização.

---

## 📞 Suporte

- Problemas de integração WAHA: revise **Base URL, API Key, Sessão**.
- Erros de view/instalação: ver seção **Problemas comuns**.
- Precisa de ajuda? Abra uma issue e anexe os logs/stacktrace.
