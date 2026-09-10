// Vercel Serverless Function - api/asaas-webhook.js
// Segurança: token obrigatório + idempotência + sem dados sensíveis expostos
import fs from 'fs';
import path from 'path';

// Registro de eventos já processados (idempotência em memória)
const processedEvents = new Set();

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
  // VALIDAÇÃO OBRIGATÓRIA DO TOKEN (Autenticação do Webhook)
  // ══════════════════════════════════════════════════════════
  const expectedToken = process.env.ASAAS_WEBHOOK_TOKEN || 'hizabellai_music_webhook_token_2036';
  const receivedToken = req.headers['asaas-access-token'] || req.headers['asaas-token'];

  if (!receivedToken) {
    console.warn('[WEBHOOK] Requisição rejeitada: token ausente');
    return res.status(401).json({ error: 'Token de autenticação ausente' });
  }

  if (receivedToken !== expectedToken) {
    console.warn('[WEBHOOK] Requisição rejeitada: token inválido');
    return res.status(403).json({ error: 'Token de autenticação inválido' });
  }

  const payload = req.body || {};
  const event = payload.event;
  const validEvents = ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'];

  if (!validEvents.includes(event)) {
    return res.status(200).json({ received: true, ignored: event });
  }

  const payment = payload.payment || {};
  const paymentId = payment.id;

  // ══════════════════════════════════════════════════════════
  // IDEMPOTÊNCIA — evita processar o mesmo evento duas vezes
  // ══════════════════════════════════════════════════════════
  const eventKey = `${event}_${paymentId}`;
  if (processedEvents.has(eventKey)) {
    console.log(`[WEBHOOK] Evento duplicado ignorado: ${eventKey}`);
    return res.status(200).json({ received: true, duplicate: true });
  }
  processedEvents.add(eventKey);

  // Limita o Set a 1000 entradas para evitar memory leak
  if (processedEvents.size > 1000) {
    const firstKey = processedEvents.values().next().value;
    processedEvents.delete(firstKey);
  }

  try {
    const dataDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

    const filePath = path.join(dataDir, 'orders.json');
    let orders = {};
    if (fs.existsSync(filePath)) {
      orders = JSON.parse(fs.readFileSync(filePath, 'utf8') || '{}');
    }

    const extRef = payment.externalReference;
    const paymentVal = parseFloat(payment.value || 0);

    let targetOrderId = null;

    if (extRef && orders[extRef]) {
      targetOrderId = extRef;
    } else {
      const desc = payment.description || '';
      const match = desc.match(/HZ-\d+/);
      if (match && orders[match[0]]) {
        targetOrderId = match[0];
      } else {
        // Fallback: pedido mais recente com mesmo valor e status PENDING
        const keys = Object.keys(orders).reverse();
        for (const k of keys) {
          if (orders[k].status === 'PENDING') {
            const val = parseFloat(orders[k].offerPrice || 0);
            if (Math.abs(val - paymentVal) < 0.5) {
              targetOrderId = k;
              break;
            }
          }
        }
      }
    }

    if (targetOrderId && orders[targetOrderId]) {
      orders[targetOrderId].status = 'PAID';
      orders[targetOrderId].paidAt = new Date().toISOString();
      orders[targetOrderId].paymentDetails = {
        paymentId,
        billingType: payment.billingType,
        value: paymentVal,
        event
      };
      fs.writeFileSync(filePath, JSON.stringify(orders, null, 2), 'utf8');
      console.log(`[WEBHOOK] ✅ Pedido ${targetOrderId} marcado como PAID`);
    }

    return res.status(200).json({ received: true, orderId: targetOrderId, status: 'PAID' });
  } catch (err) {
    console.error('[WEBHOOK] Erro interno:', err.message);
    return res.status(200).json({ received: true, error: 'Erro interno processado' });
  }
}
