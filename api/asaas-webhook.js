// Vercel Serverless Function - api/asaas-webhook.js
import fs from 'fs';
import path from 'path';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, asaas-access-token');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Validação de token se fornecido
  const expectedToken = process.env.ASAAS_WEBHOOK_TOKEN || 'hizabellai_secure_token_2026';
  const receivedToken = req.headers['asaas-access-token'] || req.headers['asaas-token'];
  if (expectedToken && receivedToken && receivedToken !== expectedToken) {
    return res.status(401).json({ error: 'Token invalido', received: false });
  }

  const payload = req.body || {};
  const event = payload.event;
  const validEvents = ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'];

  if (!validEvents.includes(event)) {
    return res.status(200).json({ received: true, ignored: event });
  }

  try {
    const dataDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
    
    const filePath = path.join(dataDir, 'orders.json');
    let orders = {};
    if (fs.existsSync(filePath)) {
      orders = JSON.parse(fs.readFileSync(filePath, 'utf8') || '{}');
    }

    const payment = payload.payment || {};
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
        // Fallback para pedido mais recente com mesmo valor
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
        paymentId: payment.id,
        billingType: payment.billingType,
        value: paymentVal,
        event
      };
      fs.writeFileSync(filePath, JSON.stringify(orders, null, 2), 'utf8');
    }

    return res.status(200).json({ received: true, orderId: targetOrderId, status: 'PAID' });
  } catch (err) {
    return res.status(200).json({ received: true, error: err.message });
  }
}
