// Vercel Serverless Function - api/create-order.js
// Segurança Sênior: ID Imprevisível + Validação Estrita de Schema/Preço + Anti-Sobrescrita (409) + Rate Limit (10/min) + CORS Restrito
import fs from 'fs';
import path from 'path';
import os from 'os';
import crypto from 'crypto';

// Rate Limiting em memória por IP (máx 10 req/min)
const rateLimitMap = new Map();

function isRateLimited(ip) {
  const now = Date.now();
  const windowMs = 60 * 1000; // 1 minuto
  const maxRequests = 10;

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

// Catálogo oficial de pacotes permitidos e faixas de preço válidas
const VALID_OFFERS = {
  p1: { name: 'Canção Acústica Simples', minPrice: 35.0, maxPrice: 45.0, defaultPrice: '37.90' },
  p2: { name: 'Canção + Clipe com Fotos (30s)', minPrice: 45.0, maxPrice: 55.0, defaultPrice: '47.00' },
  p3: { name: 'Pack Comerciante / Jingles (3 Músicas)', minPrice: 75.0, maxPrice: 89.0, defaultPrice: '79.90' },
  p4: { name: 'Produção Completa de Estúdio', minPrice: 90.0, maxPrice: 110.0, defaultPrice: '97.00' },
  p5: { name: 'Pacote Premium Emocional', minPrice: 140.0, maxPrice: 165.0, defaultPrice: '147.00' }
};

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
  // CORS Restrito aos domínios homologados
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

  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('X-Content-Type-Options', 'nosniff');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // 1. Rate Limiting (máx 10 req/min por IP)
  const clientIp = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
    || req.headers['x-real-ip']
    || req.socket?.remoteAddress
    || 'unknown';

  if (isRateLimited(clientIp)) {
    return res.status(429).json({
      error: 'Muitas requisições de criação de pedidos. Aguarde 1 minuto.',
      retryAfter: 60
    });
  }

  // 2. Parse seguro do body
  let body = req.body || {};
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch (e) { body = {}; }
  }

  // 3. Validação rigorosa de Schema e Tipos
  const { cliente, offerId, offerPrice } = body;

  if (!cliente || typeof cliente !== 'object') {
    return res.status(400).json({ error: 'Dados do cliente obrigatórios' });
  }

  const nome = typeof cliente.nome === 'string' ? cliente.nome.trim().substring(0, 100) : '';
  const homenageado = typeof cliente.homenageado === 'string' ? cliente.homenageado.trim().substring(0, 100) : '';
  const whatsapp = typeof cliente.whatsapp === 'string' ? cliente.whatsapp.trim().substring(0, 30) : '';
  const ritmo = typeof cliente.ritmo === 'string' ? cliente.ritmo.trim().substring(0, 50) : 'Acústico / MPB';
  const clima = typeof cliente.clima === 'string' ? cliente.clima.trim().substring(0, 50) : 'Emocionante';
  const resumo = typeof cliente.resumo === 'string' ? cliente.resumo.trim().substring(0, 1000) : '';

  if (!nome || !homenageado) {
    return res.status(400).json({ error: 'Nome do cliente e do homenageado são obrigatórios' });
  }

  const selectedOfferId = (typeof offerId === 'string' && VALID_OFFERS[offerId]) ? offerId : 'p2';
  const offerMeta = VALID_OFFERS[selectedOfferId];

  // Validação da faixa de preço aceitável
  const parsedPrice = parseFloat(offerPrice || offerMeta.defaultPrice);
  if (isNaN(parsedPrice) || parsedPrice < offerMeta.minPrice || parsedPrice > offerMeta.maxPrice) {
    return res.status(400).json({ error: `Faixa de preço inválida para o pacote ${selectedOfferId}` });
  }

  try {
    const orders = readOrders();

    // 4. Geração Estrita do orderId no Backend (Criptograficamente Imprevisível)
    // Padrão: HZ- + 12 caracteres hexadecimais aleatórios (ex: HZ-3A8F9E1B2C4D)
    const randomSuffix = crypto.randomBytes(6).toString('hex').toUpperCase();
    const generatedOrderId = `HZ-${randomSuffix}`;

    // 5. Verificação anti-colisão / anti-sobrescrita
    if (orders[generatedOrderId]) {
      return res.status(409).json({ error: 'Conflito de identificador de pedido. Tente novamente.' });
    }

    // 6. Persistência do novo pedido com status PENDING
    orders[generatedOrderId] = {
      orderId: generatedOrderId,
      status: 'PENDING',
      offerId: selectedOfferId,
      offerName: offerMeta.name,
      offerPrice: parsedPrice.toFixed(2),
      cliente: {
        nome,
        homenageado,
        whatsapp,
        ritmo,
        clima,
        resumo
      },
      createdAt: new Date().toISOString()
    };

    writeOrders(orders);
    console.log(`[ORDER] Pedido criado com sucesso: ${generatedOrderId} (${offerMeta.name})`);

    return res.status(200).json({
      success: true,
      orderId: generatedOrderId,
      offerId: selectedOfferId,
      offerName: offerMeta.name,
      offerPrice: parsedPrice.toFixed(2),
      status: 'PENDING'
    });
  } catch (err) {
    console.error('[ORDER] Erro interno:', err.message);
    return res.status(500).json({ error: 'Erro ao registrar pedido' });
  }
}
