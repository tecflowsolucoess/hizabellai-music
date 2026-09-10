// Vercel Serverless Function - api/create-order.js
import fs from 'fs';
import path from 'path';
import os from 'os';

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

  // Fallback local se existir
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
  // Sempre grava em /tmp (permissão garantida no Lambda/Vercel)
  try {
    fs.writeFileSync(getOrdersPath(), data, 'utf8');
  } catch (e) {}

  // Tenta gravar em data/ se não for ambiente read-only
  try {
    const localDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(localDir)) fs.mkdirSync(localDir, { recursive: true });
    fs.writeFileSync(path.join(localDir, 'orders.json'), data, 'utf8');
  } catch (e) {}
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, asaas-access-token');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  let body = req.body || {};
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch (e) { body = {}; }
  }

  const { orderId, cliente, offerId, offerPrice, offerName } = body;
  if (!orderId) {
    return res.status(400).json({ error: 'orderId obrigatorio' });
  }

  try {
    const orders = readOrders();

    orders[orderId] = {
      orderId,
      status: 'PENDING',
      offerId: offerId || 'p2',
      offerName: offerName || 'Canção + Clipe 30s',
      offerPrice: offerPrice || '47.00',
      cliente: cliente || {},
      createdAt: new Date().toISOString()
    };

    writeOrders(orders);
    return res.status(200).json({ success: true, orderId, status: 'PENDING' });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
