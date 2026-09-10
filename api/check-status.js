// Vercel Serverless Function - api/check-status.js
import fs from 'fs';
import path from 'path';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, asaas-access-token');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { orderId } = req.query;
  if (!orderId) {
    return res.status(400).json({ error: 'orderId obrigatorio' });
  }

  try {
    const filePath = path.join(process.cwd(), 'data', 'orders.json');
    if (fs.existsSync(filePath)) {
      const data = JSON.parse(fs.readFileSync(filePath, 'utf8') || '{}');
      if (data[orderId]) {
        return res.status(200).json(data[orderId]);
      }
    }
    return res.status(200).json({ orderId, status: 'PENDING', notFound: true });
  } catch (e) {
    return res.status(200).json({ orderId, status: 'PENDING' });
  }
}
