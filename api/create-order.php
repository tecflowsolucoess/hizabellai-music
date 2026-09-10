<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, asaas-access-token');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$rawInput = file_get_contents('php://input');
$data = json_decode($rawInput, true);

if (!$data || empty($data['orderId'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Dados inválidos ou orderId ausente.']);
    exit;
}

$dbFile = __DIR__ . '/../data/orders.json';
$orders = [];

if (file_exists($dbFile)) {
    $content = file_get_contents($dbFile);
    $orders = json_decode($content, true) ?: [];
}

$orderId = trim($data['orderId']);
$newOrder = [
    'orderId'     => $orderId,
    'status'      => 'PENDING',
    'offerId'     => $data['offerId'] ?? 'p2',
    'offerName'   => $data['offerName'] ?? 'Canção + Clipe 30s',
    'offerPrice'  => $data['offerPrice'] ?? '47.00',
    'cliente'     => [
        'nome'        => $data['cliente']['nome'] ?? '',
        'homenageado' => $data['cliente']['homenageado'] ?? '',
        'whatsapp'    => $data['cliente']['whatsapp'] ?? '',
        'ritmo'       => $data['cliente']['ritmo'] ?? 'Acústico / MPB',
        'clima'       => $data['cliente']['clima'] ?? 'Emocionante (Chorar)',
        'resumo'      => $data['cliente']['resumo'] ?? ''
    ],
    'createdAt'   => date('c'),
    'updatedAt'   => date('c')
];

$orders[$orderId] = $newOrder;

file_put_contents($dbFile, json_encode($orders, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);

echo json_encode([
    'success' => true,
    'orderId' => $orderId,
    'status'  => 'PENDING'
]);
