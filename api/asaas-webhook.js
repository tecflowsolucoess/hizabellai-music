// Vercel Serverless Function - api/asaas-webhook.js
// Segurança Sênior: Validação Estrita de Token (Sem Fallback) + Timing Attack Safe + Idempotência + Eliminação Total de Heurística de Valor
import fs from 'fs';
import path from 'path';
import os from 'os';
import crypto from 'crypto';

// Registro de eventos já processados (idempotência em memória)
const processedEvents = new Set();

function getOrdersPath() {
  return path.join(os.tmpdir(), 'hizabellai_orders.json');
}

function readOrders() {
  const p = getOrdersPath();
  try {
    if (fs.existsSync(p)) {
      return JSON.parse(fs.readFileSync(p, 'utf8') || '{}');
    }
  } catch (e) {}

  try {
    const local = path.join(process.cwd(), 'data', 'orders.json');
    if (fs.existsSync(local)) {
      return JSON.parse(fs.readFileSync(local, 'utf8') || '{}');
    }
  } catch (e) {}

  return {};
}

function writeOrders(orders) {
  const data = JSON.stringify(orders, null, 2);
  try {
    fs.writeFileSync(getOrdersPath(), data, 'utf8');
  } catch (e) {}

  try {
    const localDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(localDir)) fs.mkdirSync(localDir, { recursive: true });
    fs.writeFileSync(path.join(localDir, 'orders.json'), data, 'utf8');
  } catch (e) {}
}

export default async function handler(req, res) {
  // Security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, asaas-access-token');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // ══════════════════════════════════════════════════════════
  // 1. VALIDAÇÃO OBRIGATÓRIA DO TOKEN (Sem fallback hardcoded)
  // ══════════════════════════════════════════════════════════
  const expectedToken = process.env.ASAAS_WEBHOOK_TOKEN;
  if (!expectedToken) {
    console.error('[FATAL SECURITY] ASAAS_WEBHOOK_TOKEN não está definido no ambiente!');
    return res.status(500).json({ error: 'Configuração de segurança pendente no servidor' });
  }

  const receivedToken = req.headers['asaas-access-token'] || req.headers['asaas-token'];
  if (!receivedToken) {
    console.warn('[WEBHOOK] Requisição rejeitada: cabeçalho de token ausente');
    return res.status(401).json({ error: 'Token de autenticação ausente' });
  }

  // Comparação criptográfica em tempo constante (anti-timing attack)
  const bufExpected = Buffer.from(expectedToken);
  const bufReceived = Buffer.from(receivedToken);
  if (bufExpected.length !== bufReceived.length || !crypto.timingSafeEqual(bufExpected, bufReceived)) {
    console.warn('[WEBHOOK] Requisição rejeitada: token inválido');
    return res.status(403).json({ error: 'Token de autenticação inválido' });
  }

  // ══════════════════════════════════════════════════════════
  // 2. PARSE E VALIDAÇÃO DO EVENTO
  // ══════════════════════════════════════════════════════════
  let payload = req.body || {};
  if (typeof payload === 'string') {
    try { payload = JSON.parse(payload); } catch (e) { payload = {}; }
  }

  const event = payload.event;
  const validEvents = ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'];

  if (!validEvents.includes(event)) {
    return res.status(200).json({ received: true, ignored: event });
  }

  const payment = payload.payment || {};
  const paymentId = payment.id || 'unknown';

  // ══════════════════════════════════════════════════════════
  // 3. IDEMPOTÊNCIA — evita processar o mesmo evento duas vezes
  // ══════════════════════════════════════════════════════════
  const eventKey = `${event}_${paymentId}`;
  if (processedEvents.has(eventKey)) {
    console.log(`[WEBHOOK] Evento duplicado ignorado: ${eventKey}`);
    return res.status(200).json({ received: true, duplicate: true });
  }
  processedEvents.add(eventKey);

  if (processedEvents.size > 1000) {
    const firstKey = processedEvents.values().next().value;
    processedEvents.delete(firstKey);
  }

  // ══════════════════════════════════════════════════════════
  // 4. ATRIBUIÇÃO ESTRITA POR externalReference (Sem Heurística de Valor)
  // ══════════════════════════════════════════════════════════
  const extRef = payment.externalReference;
  if (!extRef || typeof extRef !== 'string') {
    console.warn(`[WEBHOOK] Pagamento ${paymentId} recebido sem externalReference. Ignorando alteração de estado.`);
    return res.status(200).json({ received: true, warning: 'unmatched_reference' });
  }

  try {
    const orders = readOrders();

    if (!orders[extRef]) {
      console.warn(`[WEBHOOK] Pagamento ${paymentId} não corresponde a nenhum pedido registrado (${extRef}).`);
      return res.status(200).json({ received: true, warning: 'unmatched_reference' });
    }

    // Marca o pedido como APROVADO
    orders[extRef].status = 'PAID';
    orders[extRef].paidAt = new Date().toISOString();
    orders[extRef].paymentDetails = {
      paymentId,
      billingType: payment.billingType,
      value: parseFloat(payment.value || 0),
      event
    };

    writeOrders(orders);
    console.log(`[WEBHOOK] ✅ Pedido ${extRef} aprovado com sucesso via Asaas`);

    return res.status(200).json({ received: true, orderId: extRef, status: 'PAID' });
  } catch (err) {
    console.error('[WEBHOOK] Erro interno:', err.message);
    return res.status(500).json({ error: 'Erro interno ao processar webhook' });
  }
}
