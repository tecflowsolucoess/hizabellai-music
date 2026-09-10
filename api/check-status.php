<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, asaas-access-token');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$orderId = isset($_GET['orderId']) ? trim($_GET['orderId']) : '';

if (!$orderId) {
    http_response_code(400);
    echo json_encode(['error' => 'Parâmetro orderId obrigatório.']);
    exit;
}

$dbFile = __DIR__ . '/../data/orders.json';

if (!file_exists($dbFile)) {
    echo json_encode(['orderId' => $orderId, 'status' => 'PENDING', 'message' => 'Nenhum pedido registrado ainda.']);
    exit;
}

$content = file_get_contents($dbFile);
$orders = json_decode($content, true) ?: [];

if (isset($orders[$orderId])) {
    $order = $orders[$orderId];
    echo json_encode([
        'orderId'   => $orderId,
        'status'    => $order['status'] ?? 'PENDING',
        'offerId'   => $order['offerId'] ?? '',
        'offerName' => $order['offerName'] ?? '',
        'cliente'   => $order['cliente'] ?? [],
        'paidAt'    => $order['paidAt'] ?? null
    ]);
} else {
    // Se ainda não foi sincronizado no backend, responde PENDING por segurança
    echo json_encode([
        'orderId' => $orderId,
        'status'  => 'PENDING',
        'notFound' => true
    ]);
}
