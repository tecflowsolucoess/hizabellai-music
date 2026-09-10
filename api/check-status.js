// Vercel Serverless Function - api/check-status.js
// Com Rate Limiting por IP (máx 60 req/min)
import fs from 'fs';
import path from 'path';

// Mapa em memória para rate limiting (reseta ao reiniciar a função)
const rateLimitMap = new Map();

function isRateLimited(ip) {
  const now = Date.now();
  const windowMs = 60 * 1000; // 1 minuto
  const maxRequests = 60;

  if (!rateLimitMap.has(ip)) {
    rateLimitMap.set(ip, { count: 1, startTime: now });
    return false;
  }

  const record = rateLimitMap.get(ip);

  // Reseta a janela se passou 1 minuto
  if (now - record.startTime > windowMs) {
    rateLimitMap.set(ip, { count: 1, startTime: now });
    return false;
  }

  record.count++;

  if (record.count > maxRequests) {
    return true; // Rate limit atingido
  }

  return false;
}

export default async function handler(req, res) {
  // Security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Access-Control-Allow-Origin', 'https://hizabellai-music.vercel.app');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // Rate Limiting por IP
  const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
    || req.headers['x-real-ip']
    || req.socket?.remoteAddress
    || 'unknown';

  if (isRateLimited(clientIp)) {
    return res.status(429).json({
      error: 'Muitas requisições. Tente novamente em 1 minuto.',
      retryAfter: 60
    });
  }

  // Valida orderId — apenas caracteres seguros
  const { orderId } = req.query;
  if (!orderId || !/^HZ-\d+$/.test(orderId)) {
    return res.status(400).json({ error: 'orderId inválido ou ausente' });
  }

  try {
    const filePath = path.join(process.cwd(), 'data', 'orders.json');
    if (fs.existsSync(filePath)) {
      const data = JSON.parse(fs.readFileSync(filePath, 'utf8') || '{}');
      if (data[orderId]) {
        // Retorna apenas campos necessários (não expõe dados sensíveis)
        const { status, paidAt } = data[orderId];
        return res.status(200).json({ orderId, status, paidAt });
      }
    }
    return res.status(200).json({ orderId, status: 'PENDING' });
  } catch (e) {
    return res.status(200).json({ orderId, status: 'PENDING' });
  }
}
