# -*- coding: utf-8 -*-
"""
Script Gerador de Relatório de Auditoria de Segurança - HizabellAi Music
Gera o arquivo: docs/security-audit/relatorio-auditoria-seguranca.pdf
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(BASE_DIR, "relatorio-auditoria-seguranca.pdf")
CHART_DONUT = os.path.join(BASE_DIR, "chart_severity_donut.png")
CHART_BAR = os.path.join(BASE_DIR, "chart_category_bar.png")

# Paleta oficial da auditoria
PALETTE = {
    'critica': '#B91C1C',
    'alta': '#EA580C',
    'media': '#D97706',
    'baixa': '#2563EB',
    'forte': '#059669',
    'bg_light': '#F8FAFC',
    'text_dark': '#0F172A',
    'text_muted': '#475569',
    'border': '#E2E8F0',
    'brand': '#4338CA'
}

def generate_charts():
    plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
    plt.rcParams['text.color'] = PALETTE['text_dark']
    plt.rcParams['axes.labelcolor'] = PALETTE['text_dark']
    plt.rcParams['xtick.color'] = PALETTE['text_dark']
    plt.rcParams['ytick.color'] = PALETTE['text_dark']

    # 1. Gráfico de Rosca (Severidade)
    labels = ['Crítica (1)', 'Alta (3)', 'Média (3)', 'Baixa/Info (2)']
    sizes = [1, 3, 3, 2]
    colors_list = [PALETTE['critica'], PALETTE['alta'], PALETTE['media'], PALETTE['baixa']]
    
    fig, ax = plt.subplots(figsize=(4.5, 3.2), subplot_kw=dict(aspect="equal"))
    wedges, texts, autotexts = ax.pie(
        sizes, autopct='%1.0f%%', pctdistance=0.75,
        colors=colors_list, startangle=140,
        wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2)
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
        autotext.set_weight('bold')
    
    ax.legend(wedges, labels, loc="center", bbox_to_anchor=(0.5, -0.15),
              ncol=2, frameon=False, fontsize=8)
    plt.title("Distribuição por Severidade", fontsize=11, fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(CHART_DONUT, dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Gráfico de Barras (Categorias)
    categories = [
        '1. Banco sem\nTranca',
        '2. Permissão no\nNavegador',
        '3. IDOR / Obj.\nReferences',
        '4. Chaves\nExpostas',
        '5. Inputs / XSS\n& Sanitização'
    ]
    vuln_counts = [1, 1, 3, 1, 1]
    bar_colors = [PALETTE['media'], PALETTE['critica'], PALETTE['alta'], PALETTE['alta'], PALETTE['baixa']]

    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    bars = ax.bar(categories, vuln_counts, color=bar_colors, width=0.55, edgecolor='none')
    ax.set_ylabel("Qtd. de Achados", fontsize=8, fontweight='bold')
    ax.set_ylim(0, 4)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.title("Achados por Categoria Auditada", fontsize=11, fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(CHART_BAR, dpi=300, bbox_inches='tight')
    plt.close()


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Capa sem cabeçalho e rodapé convencional
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor(PALETTE['text_muted']))

        # Cabeçalho
        self.drawString(2 * cm, 28.2 * cm, "Relatório de Auditoria de Segurança — HizabellAi Music")
        self.drawRightString(19 * cm, 28.2 * cm, "CONFIDENCIAL")
        self.setStrokeColor(colors.HexColor(PALETTE['border']))
        self.setLineWidth(0.5)
        self.line(2 * cm, 28.0 * cm, 19 * cm, 28.0 * cm)

        # Rodapé
        self.line(2 * cm, 1.8 * cm, 19 * cm, 1.8 * cm)
        self.drawString(2 * cm, 1.3 * cm, "TecFlow Soluções em Tecnologia | Auditoria de Código-Fonte")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19 * cm, 1.3 * cm, page_str)
        self.restoreState()


def build_pdf():
    generate_charts()

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm
    )

    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor(PALETTE['brand']),
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor(PALETTE['text_muted']),
        alignment=0
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor(PALETTE['text_dark']),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor(PALETTE['brand']),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor(PALETTE['text_dark']),
        spaceAfter=6
    )
    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F1F5F9'),
        borderPadding=4,
        spaceAfter=6
    )
    chip_critica = ParagraphStyle('ChipCrit', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#FFFFFF'))
    chip_alta = ParagraphStyle('ChipAlta', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#FFFFFF'))
    chip_media = ParagraphStyle('ChipMed', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#FFFFFF'))
    chip_baixa = ParagraphStyle('ChipBaixa', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#FFFFFF'))

    story = []

    # ══════════════════════════════════════════════════════════
    # a) CAPA
    # ══════════════════════════════════════════════════════════
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph("RELATÓRIO DE AUDITORIA DE SEGURANÇA", title_style))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("HizabellAi Music — Plataforma Transacional & Landing Page", subtitle_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor(PALETTE['brand']), spaceAfter=20))

    meta_info = [
        [Paragraph("<b>Data da Auditoria:</b>", body_style), Paragraph("10 de Setembro de 2026", body_style)],
        [Paragraph("<b>Organização / Projeto:</b>", body_style), Paragraph("tecflowsolucoess / hizabellai-music", body_style)],
        [Paragraph("<b>Ambiente em Produção:</b>", body_style), Paragraph("https://hizabellai-music.vercel.app", body_style)],
        [Paragraph("<b>Escopo Auditado:</b>", body_style), Paragraph("Código-fonte completo (index.html, api/*.js, vercel.json, .htaccess, histórico Git)", body_style)],
        [Paragraph("<b>Classificação:</b>", body_style), Paragraph("<font color='#B91C1C'><b>DOCUMENTO RESTRITO / CONFIDENCIAL</b></font>", body_style)],
    ]
    t_meta = Table(meta_info, colWidths=[4.2 * cm, 12.8 * cm])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 1.2 * cm))

    # Nota Metodológica
    story.append(Paragraph("<b>Nota Metodológica & Stack Tecnológica Detectada</b>", h2_style))
    method_text = (
        "Esta auditoria foi realizada com base na análise estática de código-fonte (SAST) e modelagem de ameaças, "
        "sem intervenção ou modificação de arquivos de código da aplicação. Antes da revisão das vulnerabilidades, a stack "
        "do projeto foi mapeada com exatidão:<br/>"
        "• <b>Linguagem & Backend:</b> JavaScript (Node.js ESM) rodando em arquitetura Serverless Functions na Vercel (AWS Lambda sob o capô).<br/>"
        "• <b>Frontend:</b> Single Page Application (HTML5, TailwindCSS via CDN, Vanilla JavaScript puro no navegador).<br/>"
        "• <b>Mecanismo de Persistência / Banco:</b> Armazenamento baseado em arquivos JSON (<code>/tmp/hizabellai_orders.json</code> e <code>data/orders.json</code>), sem banco SQL/NoSQL ou RLS nativo.<br/>"
        "• <b>Autenticação & Autorização:</b> Checkout transacional sem contas de usuário; identificação por ID de pedido (<code>orderId</code>) e token estático para validação de webhook Asaas.<br/>"
        "• <b>Infraestrutura & Deploy:</b> <code>vercel.json</code> (Vercel Edge/Serverless) e regras de compatibilidade Apache em <code>.htaccess</code>.<br/><br/>"
        "Cada uma das 5 categorias mandatárias da auditoria foi estritamente adaptada e avaliada no contexto real desta stack tecnológica."
    )
    story.append(Paragraph(method_text, body_style))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # b) RESUMO EXECUTIVO
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("1. Resumo Executivo", h1_style))
    exec_summary = (
        "A revisão de segurança identificou <b>9 achados</b> técnicos, categorizados em 1 Crítica, 3 Altas, 3 Médias e 2 Baixas/Informativas. "
        "O sistema apresenta uma postura louvável de <b>defesa em profundidade</b> no frontend e cabeçalhos HTTP, incluindo políticas modernas de "
        "segurança (CSP, HSTS, X-Frame-Options: DENY) e uso sistemático de <code>textContent</code> para evitar injeções XSS diretas no DOM. "
        "No entanto, o risco primordial reside no <b>desacoplamento de autorização entre o navegador e o webhook</b>: o fluxo pós-pagamento "
        "libera o atendimento VIP e marca o pedido como aprovado no cliente com base exclusivamente em parâmetros de URL "
        "(<code>?status=pago</code>), permitindo acesso não autorizado aos serviços sem comprovação financeira prévia."
    )
    story.append(Paragraph(exec_summary, body_style))
    story.append(Spacer(1, 0.4 * cm))

    # Tabela com gráficos lado a lado
    chart_table_data = [
        [Image(CHART_DONUT, width=7.5*cm, height=5.3*cm), Image(CHART_BAR, width=9.2*cm, height=5.3*cm)]
    ]
    t_charts = Table(chart_table_data, colWidths=[8.0*cm, 9.0*cm])
    t_charts.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_charts)
    story.append(Spacer(1, 0.6 * cm))

    # ══════════════════════════════════════════════════════════
    # c) PONTOS FORTES E PONTOS FRACOS
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("2. Avaliação de Postura: Pontos Fortes e Riscos Centrais", h1_style))
    
    strong_points = [
        [Paragraph("<b>Ponto Forte Verificado (Evidência Real)</b>", body_bold), Paragraph("<b>Impacto Positivo na Segurança</b>", body_bold)],
        [
            Paragraph("<b>Defesa Anti-XSS via DOM textContent:</b><br/><code>index.html:1167-1466</code>", body_style),
            Paragraph("Todas as interpolações dinâmicas de texto (título da faixa, contadores, identificador de pedido, nome do cliente e homenageado) utilizam <code>element.textContent</code> ao invés de <code>innerHTML</code>, anulando a execução de scripts em injeções DOM-based.", body_style)
        ],
        [
            Paragraph("<b>Blindagem Completa de Headers HTTP:</b><br/><code>vercel.json:10-37</code>", body_style),
            Paragraph("Implementação ativa de <code>X-Frame-Options: DENY</code> (proteção contra Clickjacking), <code>Strict-Transport-Security</code> (HSTS com preload), <code>nosniff</code>, <code>Referrer-Policy</code> e <code>Permissions-Policy</code> restritivo.", body_style)
        ],
        [
            Paragraph("<b>Validação Criptográfica de Formato & Rate Limit:</b><br/><code>api/check-status.js:7-68</code>", body_style),
            Paragraph("A rota de checagem implementa Rate Limiting por IP (máx 60 req/min) e valida o <code>orderId</code> com expressão regular estrita (<code>/^HZ-\\d+$/</code>), barrando SQLi, path traversal e injeções de caracteres anômalos.", body_style)
        ],
        [
            Paragraph("<b>Idempotência e Não-Exposição em Webhook:</b><br/><code>api/asaas-webhook.js:53-64, 117-120</code>", body_style),
            Paragraph("O webhook do Asaas possui cache de idempotência contra repetições fraudulentas e mascara erros internos, respondendo com mensagens genéricas sem vazamento de stack traces ou caminhos de servidor.", body_style)
        ]
    ]
    t_strong = Table(strong_points, colWidths=[6.0*cm, 11.0*cm])
    t_strong.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ECFDF5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#065F46')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A7F3D0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_strong)
    story.append(Spacer(1, 0.4 * cm))

    weak_points = (
        "<b>Riscos Centrais (Pontos Fracos):</b><br/>"
        "1. <b>Bypass de Autorização Client-Side:</b> A liberação da UI de pagamento aprovado e do botão de atendimento WhatsApp "
        "baseia-se na presença de strings na URL, tornando o controle contornável por qualquer visitante.<br/>"
        "2. <b>Sobrescrita Arbitrária de Pedidos (IDOR):</b> O backend aceita o identificador de pedido fornecido no corpo da requisição sem "
        "validar se a chave já existe, permitindo que terceiros sobrescrevam e invalidem pedidos de outros usuários.<br/>"
        "3. <b>Token de Webhook em Código (Chave Exposta):</b> Fallback hardcoded em <code>api/asaas-webhook.js</code> exposto no histórico do repositório Git."
    )
    story.append(Paragraph(weak_points, body_style))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # d) TABELA DE ACHADOS DETALHADOS POR CATEGORIA
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("3. Tabela Detalhada de Achados por Categoria", h1_style))

    def make_chip(label, bg_color):
        return Table([[Paragraph(f"<b>{label}</b>", ParagraphStyle('CP', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.white, alignment=1))]],
                     colWidths=[1.8*cm], rowHeights=[0.55*cm],
                     style=[
                         ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
                         ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                         ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                         ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                         ('TOPPADDING', (0,0), (-1,-1), 0),
                     ])

    findings_table = [
        [
            Paragraph("<b>Sev.</b>", body_bold),
            Paragraph("<b>Arquivo : Linhas</b>", body_bold),
            Paragraph("<b>Vulnerabilidade & Causa Raiz</b>", body_bold),
            Paragraph("<b>Categoria</b>", body_bold)
        ],
        [
            make_chip("CRÍTICA", PALETTE['critica']),
            Paragraph("<code>index.html</code><br/>L:1586-1620", body_style),
            Paragraph("<b>Bypass de Autorização no Navegador:</b> O estado de aprovação e o botão WhatsApp são liberados via parâmetro de URL (<code>?status=pago</code> ou <code>#sucesso</code>) sem confirmação do backend.", body_style),
            Paragraph("2. Permissão no Navegador", body_style)
        ],
        [
            make_chip("ALTA", PALETTE['alta']),
            Paragraph("<code>api/create-order.js</code><br/>L:58-69", body_style),
            Paragraph("<b>IDOR / Sobrescrita Arbitrária de Pedidos:</b> A função aceita qualquer <code>orderId</code> enviado pelo cliente e sobrescreve o pedido existente no JSON sem verificar existência prévia.", body_style),
            Paragraph("3. IDOR", body_style)
        ],
        [
            make_chip("ALTA", PALETTE['alta']),
            Paragraph("<code>api/asaas-webhook.js</code><br/>L:64", body_style),
            Paragraph("<b>Segredo Padrão Hardcoded:</b> Fallback público <code>'hizabellai_music_webhook_token_2036'</code> permite forjar notificações caso a variável de ambiente falhe.", body_style),
            Paragraph("4. Chaves Expostas", body_style)
        ],
        [
            make_chip("ALTA", PALETTE['alta']),
            Paragraph("<code>api/asaas-webhook.js</code><br/>L:93-102", body_style),
            Paragraph("<b>Race Condition Lógica / Atribuição Cruzada:</b> Pagamento sem referência externa é associado por aproximação de valor ao pedido mais recente, podendo aprovar pedido de usuário divergente.", body_style),
            Paragraph("3. IDOR / Lógica", body_style)
        ],
        [
            make_chip("MÉDIA", PALETTE['media']),
            Paragraph("<code>.htaccess</code><br/>L:1-14", body_style),
            Paragraph("<b>Falta de Isolamento de Diretório no Apache:</b> Não há bloqueio de leitura direta para <code>/data/orders.json</code> caso a aplicação seja hospedada em Apache/XAMPP.", body_style),
            Paragraph("1. Banco sem Tranca", body_style)
        ],
        [
            make_chip("MÉDIA", PALETTE['media']),
            Paragraph("<code>api/create-order.js</code><br/>L:43, 50-60", body_style),
            Paragraph("<b>CORS Irrestrito e Ausência de Rate Limit:</b> <code>Access-Control-Allow-Origin: *</code> e falta de controle de taxa em rota de escrita favorecem DoS por saturação de disco.", body_style),
            Paragraph("1. Isolamento & DoS", body_style)
        ],
        [
            make_chip("MÉDIA", PALETTE['media']),
            Paragraph("<code>api/check-status.js</code><br/>L:65-80", body_style),
            Paragraph("<b>Enumeração de Pedidos por ID Preditivo:</b> O uso de timestamp sequencial em <code>HZ-timestamp</code> permite que invasores mapeiem o volume e status de pedidos alheios.", body_style),
            Paragraph("3. IDOR (Leitura)", body_style)
        ],
        [
            make_chip("BAIXA", PALETTE['baixa']),
            Paragraph("<code>vercel.json</code><br/>L:35", body_style),
            Paragraph("<b>CSP Permissivo ('unsafe-inline'):</b> Diretiva de script permite execução inline, diminuindo o isolamento contra vetores de Cross-Site Scripting.", body_style),
            Paragraph("5. Inputs / XSS", body_style)
        ],
        [
            make_chip("INFO", PALETTE['baixa']),
            Paragraph("<code>index.html</code><br/>L:1504-1516", body_style),
            Paragraph("<b>Sanitização Baseada em Expressões Regulares:</b> Função artesanal com <code>replace()</code> simples em vez de biblioteca padrão de segurança (ex: DOMPurify).", body_style),
            Paragraph("5. Inputs / XSS", body_style)
        ],
    ]

    t_findings = Table(findings_table, colWidths=[2.0*cm, 3.2*cm, 8.8*cm, 3.0*cm])
    t_findings.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_findings)
    story.append(Spacer(1, 0.6 * cm))

    # ══════════════════════════════════════════════════════════
    # e) RECOMENDAÇÕES PRIORIZADAS (P1, P2, P3...)
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("4. Plano de Ação e Recomendações Priorizadas", h1_style))
    recs = [
        ("P1 (Imediato - Risco Financeiro)", "Remover a aprovação de status de pagamento baseada exclusivamente em parâmetros de URL no frontend (<code>index.html</code>). O desbloqueio do atendimento WhatsApp deve depender exclusivamente de validação assinada via HMAC ou confirmação assíncrona recebida no endpoint de checagem."),
        ("P2 (Crítico - Integridade & Credenciais)", "Eliminar o segredo default hardcoded em <code>api/asaas-webhook.js</code>, forçando a função a rejeitar inicialização se <code>process.env.ASAAS_WEBHOOK_TOKEN</code> não estiver configurado. No <code>api/create-order.js</code>, impedir que o cliente forneça o <code>orderId</code>, gerando UUID v4 exclusivo e imprevisível no backend."),
        ("P3 (Alto - Defesa em Profundidade)", "Remover a lógica de atribuição arbitrária por proximidade de valor no webhook. Se o pagamento não contiver <code>externalReference</code> correspondente, colocar o evento em quarentena ou notificar logs de auditoria."),
        ("P4 (Médio - Infraestrutura & DoS)", "Adicionar regra de bloqueio em <code>.htaccess</code> para impedir o acesso HTTP direto ao diretório <code>/data/</code> e arquivos <code>.json</code>. Implementar Rate Limiting por IP em <code>api/create-order.js</code> e restringir o CORS da API à origem exata da plataforma.")
    ]
    for p_label, p_desc in recs:
        p_text = f"<b>{p_label}:</b> {p_desc}"
        story.append(Paragraph(p_text, body_style))
    
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # f) SEÇÃO ISSUES PARA O GITHUB
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("5. Issues Acionáveis para o GitHub", h1_style))
    story.append(Paragraph(
        "Os blocos abaixo estão prontos para serem copiados diretamente para o GitHub Issues do repositório, "
        "fornecendo aos desenvolvedores todas as evidências, critérios de aceite e código de correção necessário.",
        body_style
    ))
    story.append(Spacer(1, 0.3 * cm))

    issues = [
        {
            "num": 1,
            "title": "[Segurança] Bypass de autorização de pagamento via query string no frontend",
            "labels": "security, severidade:crítica, auth",
            "desc": "O frontend da landing page libera a tela de pagamento aprovado e o botão do WhatsApp com status de pedido APROVADO ✓ se a URL contiver '?status=pago', '?status=approved' ou '#sucesso'. Qualquer usuário mal-intencionado pode navegar até esse link sem efetuar o pagamento no Asaas e forçar a liberação do atendimento.",
            "evidence": "Arquivo: index.html (Linhas 1586-1620)\nTrecho:\nconst isDirectPaid = params.get('status') === 'pago' || params.get('status') === 'approved' ...;\nif (isDirectPaid) {\n  pedido.status = 'PAID';\n  renderPaidSuccess(orderId, pedido);\n}",
            "impact": "Fraude financeira: clientes conseguem atendimento de produção musical sem confirmação de compensação bancária.",
            "fix": "Exigir que a liberação do WhatsApp dependa exclusivamente da resposta da API 'api/check-status' (consultando o status gravado pelo webhook autêntico do Asaas), ou de um token de sessão assinado.",
            "checklist": "- [ ] Remover validação direta de 'status=pago' para liberação do botão verde do WhatsApp\n- [ ] Manter o modal em estado PENDING até que 'api/check-status' retorne 'PAID'\n- [ ] Testar acesso manual a '?status=pago' e garantir que o botão WhatsApp não seja desbloqueado"
        },
        {
            "num": 2,
            "title": "[Segurança] IDOR e sobrescrita arbitrária de pedidos em api/create-order.js",
            "labels": "security, severidade:alta, idor",
            "desc": "O endpoint 'api/create-order.js' aceita o 'orderId' diretamente do corpo JSON da requisição e não verifica se a chave já existe no arquivo de pedidos. Um invasor pode enviar requisições com IDs de pedidos de outras pessoas e sobrescrever dados cadastrais ou reverter o status de PAID para PENDING.",
            "evidence": "Arquivo: api/create-order.js (Linhas 58-69)\nTrecho:\nconst orders = readOrders();\norders[orderId] = {\n  orderId,\n  status: 'PENDING',\n  cliente: cliente || {},\n  ...\n};\nwriteOrders(orders);",
            "impact": "Adulteração de dados, negação de serviço para clientes legítimos e quebra da integridade dos pedidos.",
            "fix": "Gerar o 'orderId' obrigatoriamente no servidor utilizando 'crypto.randomUUID()' e rejeitar requisições de criação de pedidos cujo ID já esteja registrado.",
            "checklist": "- [ ] Gerar ID único imprevisível no backend (UUID v4 / nanoid)\n- [ ] Impedir sobrescrita de pedidos existentes retornando 409 Conflict se o ID já existir\n- [ ] Validar schema e faixas de preço aceitáveis dos pacotes no backend"
        },
        {
            "num": 3,
            "title": "[Segurança] Segredo de autenticação padrão hardcoded em api/asaas-webhook.js",
            "labels": "security, severidade:alta, credentials",
            "desc": "O webhook do Asaas possui um token de fallback estático codificado diretamente no arquivo ('hizabellai_music_webhook_token_2036'). Caso a variável de ambiente não seja injetada ou ocorra erro de carregamento no runtime serverless, qualquer agente externo pode enviar notificações forjadas de pagamento.",
            "evidence": "Arquivo: api/asaas-webhook.js (Linha 64)\nTrecho:\nconst expectedToken = process.env.ASAAS_WEBHOOK_TOKEN || 'hizabellai_music_webhook_token_2036';",
            "impact": "Falsificação de eventos de pagamento confirmados, permitindo que atacantes aprovem transações inexistentes.",
            "fix": "Rejeitar a requisição com erro 500 caso a variável process.env.ASAAS_WEBHOOK_TOKEN não esteja definida. Rotacionar imediatamente o token atual e registrar um novo valor secreto exclusivamente nas variáveis da Vercel e Asaas.",
            "checklist": "- [ ] Remover o valor default em texto plano do código-fonte\n- [ ] Adicionar validação 'if (!process.env.ASAAS_WEBHOOK_TOKEN) throw new Error(...)'\n- [ ] Rotacionar a credencial no painel do Asaas e na Vercel"
        },
        {
            "num": 4,
            "title": "[Segurança] Race condition e atribuição cruzada de pagamentos no webhook",
            "labels": "security, severidade:alta, business-logic",
            "desc": "Quando o Asaas envia um webhook sem externalReference válida, o handler executa um fallback que busca o pedido mais recente com status PENDING e valor monetário similar (+/- R$ 0,50). Se dois pedidos forem gerados em momentos próximos com o mesmo plano, o pagamento de um cliente aprovará o pedido de outro.",
            "evidence": "Arquivo: api/asaas-webhook.js (Linhas 93-102)\nTrecho:\nfor (const k of keys) {\n  if (orders[k].status === 'PENDING') {\n    const val = parseFloat(orders[k].offerPrice || 0);\n    if (Math.abs(val - paymentVal) < 0.5) {\n      targetOrderId = k;\n      break;\n    }\n  }\n}",
            "impact": "Atribuição incorreta de pedidos, estornos e inconsistências financeiras graves.",
            "fix": "Exigir estritamente que o link de pagamento ou cobrança do Asaas carregue a referência externa do pedido ou utilizar metadados persistentes, rejeitando aprovações heurísticas baseadas em aproximação de preço.",
            "checklist": "- [ ] Remover a lógica de fallback por aproximação de valor\n- [ ] Registrar pedidos não identificados em fila de auditoria manual\n- [ ] Assegurar que os links de checkout do Asaas passem o parâmetro de externalReference"
        },
        {
            "num": 5,
            "title": "[Segurança] Diretório /data/ exposto e sem restrição de acesso em ambiente Apache",
            "labels": "security, severidade:média, info-disclosure",
            "desc": "O arquivo .htaccess não contém regras para restringir a listagem ou o download de arquivos sensíveis na pasta 'data/'. Se o projeto for executado sob um servidor Apache padrão (como XAMPP), o arquivo 'data/orders.json' fica publicamente acessível para download direto pela web.",
            "evidence": "Arquivo: .htaccess (Linhas 1-14)\nAusência de diretivas de bloqueio a arquivos .json ou pasta /data/.",
            "impact": "Vazamento em massa de dados confidenciais de clientes (nome, telefone WhatsApp, mensagens pessoais e preferências musicais).",
            "fix": "Inserir diretiva de bloqueio explícito no .htaccess: '<FilesMatch \"\\.(json|log)$\"> Require all denied </FilesMatch>'.",
            "checklist": "- [ ] Adicionar bloqueio de arquivos .json no .htaccess\n- [ ] Testar requisição direta a /data/orders.json e verificar retorno 403 Forbidden\n- [ ] Garantir que em produção na Vercel o diretório data não seja servido estaticamente"
        }
    ]

    for iss in issues:
        iss_box = [
            [Paragraph(f"<b>--- ISSUE {iss['num']} ---</b>", body_bold)],
            [Paragraph(f"<b>Título:</b> {iss['title']}", body_style)],
            [Paragraph(f"<b>Labels sugeridas:</b> <code>{iss['labels']}</code>", body_style)],
            [Paragraph(f"<b>Descrição:</b> {iss['desc']}", body_style)],
            [Paragraph(f"<b>Evidência:</b><br/><font face='Courier' size='7'>{iss['evidence'].replace(chr(10), '<br/>')}</font>", body_style)],
            [Paragraph(f"<b>Impacto:</b> {iss['impact']}", body_style)],
            [Paragraph(f"<b>Sugestão de Correção:</b> {iss['fix']}", body_style)],
            [Paragraph(f"<b>Critérios de Aceite:</b><br/>{iss['checklist'].replace(chr(10), '<br/>')}", body_style)],
            [Paragraph(f"<b>--- FIM ISSUE {iss['num']} ---</b>", body_bold)]
        ]
        t_iss = Table(iss_box, colWidths=[17.0*cm])
        t_iss.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(KeepTogether([t_iss, Spacer(1, 0.4*cm)]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso em: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
