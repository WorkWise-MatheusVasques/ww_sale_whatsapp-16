# -*- coding: utf-8 -*-
import base64
import logging
import os
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import requests
    from requests import exceptions as req_exc
except Exception:  # pragma: no cover
    requests = None
    req_exc = None


def _to_b64_str(v):
    """Garante string base64 ASCII a partir de bytes/memoryview/str."""
    if v is None:
        return ""
    if isinstance(v, memoryview):
        v = v.tobytes()
    if isinstance(v, bytes):
        try:
            # já é base64 em bytes
            return v.decode("ascii")
        except UnicodeDecodeError:
            # bytes crus -> codifica para base64
            return base64.b64encode(v).decode("ascii")
    # se já for str
    return str(v)


class WhatsappCompose(models.TransientModel):
    _name = "ww.whatsapp.compose"
    _description = "Compor WhatsApp (WAHA Plus)"

    # contexto
    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)

    # dados
    partner_id = fields.Many2one("res.partner", string="Contato")
    phone = fields.Char("Telefone (E.164 ou só dígitos ou chatId @c.us)", required=True)
    message = fields.Text("Mensagem")
    attachment_ids = fields.Many2many("ir.attachment", string="Anexos")

    # info
    session = fields.Char("Sessão WAHA", readonly=True)

    # ---------------- cfg / util ----------------
    @api.model
    def _cfg(self):
        """Carrega da definição de serviço padrão; se não houver, cai no ir.config_parameter/env."""
        # 1) Tenta serviço padrão ativo
        Svc = self.env["ww.service.definition"].sudo()
        svc = Svc.search([("active", "=", True)], order="is_default desc, id desc", limit=1)
        if svc:
            return svc.to_cfg_dict()

        # 2) Fallback para parâmetros/ENV (compat anterior)
        ICP = self.env["ir.config_parameter"].sudo()
        base = ICP.get_param("waha.base_url") or os.getenv("WAHA_URL", "")
        api_key = ICP.get_param("waha.api_key") or os.getenv("WAHA_API_KEY", "")
        session = ICP.get_param("waha.session") or os.getenv("WAHA_SESSION_ID", "default")
        timeout = int(ICP.get_param("waha.timeout", default=os.getenv("WAHA_TIMEOUT", "60")))
        if not base:
            raise UserError(_("Configure um Serviço WAHA em Configurações › Workwise › Serviços WAHA, "
                            "ou defina 'waha.base_url'/WAHA_URL no ambiente."))
        return {
            "base": base.rstrip("/"),
            "api_key": api_key,
            "session": session,
            "timeout": timeout,
            "file_transport": "data",
        }

    @api.model
    def _sanitize_phone(self, phone):
        return re.sub(r"\D+", "", phone or "")

    def _waha_headers(self, api_key):
        h = {"Content-Type": "application/json"}
        if api_key:
            h["X-Api-Key"] = api_key
        return h

    # ---------------- WAHA ----------------
    def _waha_check_exists(self, cfg, phone_digits):
        """GET /api/contacts/check-exists -> chatId"""
        url = f"{cfg['base']}/api/contacts/check-exists"
        params = {"phone": phone_digits, "session": cfg["session"]}
        try:
            r = requests.get(url, headers=self._waha_headers(cfg["api_key"]),
                             params=params, timeout=cfg["timeout"])
            r.raise_for_status()
        except Exception as e:
            if req_exc and isinstance(e, req_exc.ConnectionError):
                raise UserError(_("Não foi possível conectar ao WAHA em %s.") % cfg["base"]) from e
            if req_exc and isinstance(e, req_exc.Timeout):
                raise UserError(_("Timeout ao acessar o WAHA (%s s).") % cfg["timeout"]) from e
            raise UserError(_("Falha HTTP ao chamar WAHA: %s") % (str(e),)) from e

        data = r.json() or {}
        if not data.get("numberExists"):
            raise UserError(_("Número não está no WhatsApp ou é inválido."))
        chat_id = data.get("chatId")
        if not chat_id:
            raise UserError(_("WAHA não retornou chatId."))
        return chat_id

    def _waha_send_file_data(self, cfg, chat_id, filename, data_b64, caption, mimetype="application/pdf"):
        """POST /api/sendFile com file.data (base64)."""
        url = f"{cfg['base']}/api/sendFile"
        payload = {
            "session": cfg["session"],
            "chatId": chat_id,
            "caption": (caption or "")[:1024],
            "file": {
                "mimetype": mimetype or "application/pdf",
                "filename": filename,
                "data": data_b64,  # string base64
            },
        }
        try:
            r = requests.post(url, headers=self._waha_headers(cfg["api_key"]),
                              json=payload, timeout=cfg["timeout"])
            r.raise_for_status()
        except Exception as e:
            if req_exc and isinstance(e, req_exc.ConnectionError):
                raise UserError(_("Não foi possível conectar ao WAHA em %s.") % cfg["base"]) from e
            if req_exc and isinstance(e, req_exc.Timeout):
                raise UserError(_("Timeout ao enviar arquivo para o WAHA (%s s).") % cfg["timeout"]) from e
            raise UserError(_("Falha HTTP ao enviar pelo WAHA: %s") % (str(e),)) from e
        return r.json()

    # ---------------- PDF (defensivo) ----------------
    @api.model
    def _render_main_pdf_for(self, res_model, res_id):
        """Gera o PDF do registro de origem (Odoo 16)."""
        if res_model != "sale.order":
            raise UserError(_("Modelo não suportado: %s") % res_model)

        report_name = "sale.report_saleorder"
        report = self.env.ref("sale.action_report_saleorder", raise_if_not_found=False)

        if not report or not report.exists():
            # Fallback para a busca pelo nome técnico se o ref falhar
            report = self.env["ir.actions.report"].search([("report_name", "=", report_name)], limit=1)
            if not report:
                raise UserError(_("Relatório de Pedido de Venda ('%s') não encontrado. Verifique se o app 'Vendas' está instalado corretamente.") % report_name)

        # AQUI ESTÁ A CORREÇÃO PRINCIPAL
        pdf_bytes = self.env['ir.actions.report']._render_qweb_pdf(report_name, [res_id])[0]

        sale = self.env["sale.order"].browse(res_id)
        filename = f"Pedido_{(sale.name or 'pedido').replace('/', '_')}.pdf"
        return filename, pdf_bytes

    # ---------------- defaults ----------------
    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)

        # registro ativo
        res_model = (
            self.env.context.get("active_model")
            or vals.get("res_model")
            or self.env.context.get("default_res_model")
        )
        res_id = (
            self.env.context.get("active_id")
            or vals.get("res_id")
            or self.env.context.get("default_res_id")
        )
        if not res_id and self.env.context.get("active_ids"):
            res_id = self.env.context["active_ids"][0]

        # ---- Fallbacks visíveis no wizard ----
        if not vals.get("partner_id"):
            pid = self.env.context.get("default_partner_id")
            if not pid and res_model == "sale.order" and res_id:
                pid = self.env["sale.order"].browse(res_id).partner_id.id
            if pid:
                vals["partner_id"] = pid

        if not vals.get("phone"):
            ph = self.env.context.get("default_phone")
            if ph:
                vals["phone"] = ph
        if not vals.get("message"):
            msg = self.env.context.get("default_message")
            if msg:
                vals["message"] = msg

        # ---- Anexo automático do PDF (como no e-mail) ----
        if res_model == "sale.order" and res_id:
            filename, pdf_bytes = self._render_main_pdf_for(res_model, res_id)
            Attachment = self.env["ir.attachment"].sudo()
            attach = Attachment.search([
                ("res_model", "=", res_model),
                ("res_id", "=", res_id),
                ("name", "=", filename),
                ("mimetype", "=", "application/pdf"),
            ], limit=1)
            if not attach:
                attach = Attachment.create({
                    "name": filename,
                    "datas": base64.b64encode(pdf_bytes).decode("ascii"),
                    "mimetype": "application/pdf",
                    "res_model": res_model,
                    "res_id": res_id,
                })
            vals["attachment_ids"] = [(6, 0, [attach.id])]

        # sessão WAHA
        try:
            vals["session"] = self._cfg()["session"]
        except Exception:
            pass

        # persiste res_model/res_id no wizard
        if res_model:
            vals["res_model"] = res_model
        if res_id:
            vals["res_id"] = res_id

        return vals

    # ---------------- enviar ----------------
    def action_send(self):
        if requests is None:
            raise UserError(_("A biblioteca 'requests' não está disponível no servidor."))
        self.ensure_one()

        to_input = (self.phone or "").strip()
        if not to_input:
            raise UserError(_("Informe o telefone ou o chatId (ex.: 5511...@c.us)."))

        cfg = self._cfg()

        # aceita chatId direto (@c.us/@g.us) ou resolve via check-exists
        if "@c.us" in to_input or "@g.us" in to_input:
            chat_id = to_input
        else:
            chat_id = self._waha_check_exists(cfg, self._sanitize_phone(to_input))

        # garante anexo (se o usuário removeu, renderiza novamente)
        attach = self.attachment_ids[:1]
        if not attach or not attach.datas:
            filename, pdf_bytes = self._render_main_pdf_for(self.res_model, self.res_id)
            data_b64 = base64.b64encode(pdf_bytes).decode("ascii")
            Attachment = self.env["ir.attachment"].sudo()
            attach = Attachment.create({
                "name": filename,
                "datas": data_b64,
                "mimetype": "application/pdf",
                "res_model": self.res_model,
                "res_id": self.res_id,
            })
        else:
            filename = attach.name
            data_b64 = _to_b64_str(attach.datas)
            if not (attach.mimetype or "").startswith("application/"):
                attach.write({"mimetype": "application/pdf"})

        self._waha_send_file_data(
            cfg, chat_id, filename, data_b64, self.message, mimetype=attach.mimetype or "application/pdf"
        )

        rec = self.env[self.res_model].browse(self.res_id)
        rec.message_post(
            body=_("WhatsApp (WAHA) enviado para <b>%s</b> (chatId: %s).") % (self.phone, chat_id),
            attachment_ids=self.attachment_ids.ids,
            subtype_xmlid="mail.mt_note",
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("WhatsApp"),
                "message": _("Enviado com sucesso."),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }