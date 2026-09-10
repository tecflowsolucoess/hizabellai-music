// Vercel Serverless Function - api/check-status.js
// Segurança Sênior: Validação Estrita de ID + Proteção de Dados (Data Minimization) + Rate Limiting por IP + CORS Restrito
import fs from 'fs';
import path from 'path';
import os from 'os';

// Mapa em memória para rate limiting (60 req/min por IP)
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
  if (now - record.startTime > windowMs) {
    rateLimitMap.set(ip, { count: 1, startTime: now });
    return false;
  }

  record.count++;
  if (record.count > maxRequests) {
    return true;
  }

  return false;
}

export default async function handler(req, res) {
  // CORS Restrito aos domínios autorizados
  const allowedOrigins = [
    'https://hizabellai-music.vercel.app',
    'https://hizabellaimusic.com.br',
    'http://localhost:3000',
    'http://localhost'
  ];
  const origin = req.headers.origin;
  if (allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  } else {
    res.setHeader('Access-Control-Allow-Origin', 'https://hizabellai-music.vercel.app');
  }

  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // 1. Rate Limiting por IP
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

  // 2. Validação do orderId — padrão imprevisível seguro (HZ- + alfanumérico)
  const { orderId } = req.query;
  if (!orderId || typeof orderId !== 'string' || !/^HZ-[A-Za-z0-9_-]{6,64}$/.test(orderId)) {
    return res.status(400).json({ error: 'orderId inválido ou ausente' });
  }

  try {
    const tmpPath = path.join(os.tmpdir(), 'hizabellai_orders.json');
    const localPath = path.join(process.cwd(), 'data', 'orders.json');
    let data = {};

    if (fs.existsSync(tmpPath)) {
      try { data = JSON.parse(fs.readFileSync(tmpPath, 'utf8') || '{}'); } catch (e) {}
    } else if (fs.existsSync(localPath)) {
      try { data = JSON.parse(fs.readFileSync(localPath, 'utf8') || '{}'); } catch (e) {}
    }

    if (data[orderId]) {
      // Retorna estritamente o status público necessário (Data Minimization - sem dados pessoais de cliente)
      const { status, paidAt } = data[orderId];
      return res.status(200).json({
        orderId,
        status: status || 'PENDING',
        paidAt: paidAt || null
      });
    }

    return res.status(200).json({ orderId, status: 'PENDING', paidAt: null });
  } catch (e) {
    console.error('[CHECK-STATUS] Erro ao consultar pedido:', e.message);
    return res.status(200).json({ orderId, status: 'PENDING', paidAt: null });
  }
}
