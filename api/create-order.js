// Vercel Serverless Function - api/create-order.js
import fs from 'fs';
import path from 'path';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, asaas-access-token');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { orderId, cliente, offerId, offerPrice, offerName } = req.body || {};
  if (!orderId) {
    return res.status(400).json({ error: 'orderId obrigatorio' });
  }

  try {
    const dataDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
    
    const filePath = path.join(dataDir, 'orders.json');
    let orders = {};
    if (fs.existsSync(filePath)) {
      orders = JSON.parse(fs.readFileSync(filePath, 'utf8') || '{}');
    }

    orders[orderId] = {
      orderId,
      status: 'PENDING',
      offerId: offerId || 'p2',
      offerName: offerName || 'Canção + Clipe 30s',
      offerPrice: offerPrice || '47.00',
      cliente: cliente || {},
      createdAt: new Date().toISOString()
    };

    fs.writeFileSync(filePath, JSON.stringify(orders, null, 2), 'utf8');
    return res.status(200).json({ success: true, orderId, status: 'PENDING' });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
