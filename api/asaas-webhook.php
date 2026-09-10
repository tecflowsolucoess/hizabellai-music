<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, asaas-access-token');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 1. TOKEN DE SEGURANÇA (Configure no Asaas ou no .env se desejar)
// Se você definir um token no painel do Asaas, coloque o mesmo valor aqui:
$EXPECTED_TOKEN = getenv('ASAAS_WEBHOOK_TOKEN') ?: 'hizabellai_secure_token_2026';

// Validação opcional de cabeçalho: se o token estiver configurado, checa o header
$receivedToken = $_SERVER['HTTP_ASAAS_ACCESS_TOKEN'] ?? $_SERVER['HTTP_ASAAS_TOKEN'] ?? '';
if (!empty($EXPECTED_TOKEN) && !empty($receivedToken) && $receivedToken !== $EXPECTED_TOKEN) {
    http_response_code(401);
    echo json_encode(['error' => 'Token do webhook inválido.', 'received' => false]);
    exit;
}

// 2. RECEBE E DECODIFICA O PAYLOAD DO ASAAS
$rawPayload = file_get_contents('php://input');
$payload = json_decode($rawPayload, true);

if (!$payload) {
    http_response_code(400);
    echo json_encode(['error' => 'Payload JSON vazio ou malformado.']);
    exit;
}

// Registra log para auditoria em data/webhook_log.json
$logFile = __DIR__ . '/../data/webhook_log.json';
$logEntry = [
    'timestamp' => date('c'),
    'event'     => $payload['event'] ?? 'UNKNOWN',
    'payload'   => $payload
];
$existingLogs = file_exists($logFile) ? json_decode(file_get_contents($logFile), true) ?: [] : [];
array_unshift($existingLogs, $logEntry);
if (count($existingLogs) > 100) $existingLogs = array_slice($existingLogs, 0, 100);
@file_put_contents($logFile, json_encode($existingLogs, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);

// 3. TRATA APENAS EVENTOS DE SUCESSO DE PAGAMENTO
$event = $payload['event'] ?? '';
$validEvents = ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'];

if (!in_array($event, $validEvents, true)) {
    // Para outros eventos (ex: boleto gerado, cobrança criada), apenas confirma recebimento
    echo json_encode(['received' => true, 'ignored_event' => $event]);
    exit;
}

$payment = $payload['payment'] ?? [];
$paymentId = $payment['id'] ?? '';
$paymentValue = (float)($payment['value'] ?? 0);
$billingType = $payment['billingType'] ?? 'PIX';
$extRef = trim($payment['externalReference'] ?? '');

// 4. LOCALIZA O PEDIDO NO BANCO DE DADOS
$dbFile = __DIR__ . '/../data/orders.json';
$orders = file_exists($dbFile) ? json_decode(file_get_contents($dbFile), true) ?: [] : [];

$targetOrderId = null;

// A) Busca direta pela externalReference (se enviada no Asaas)
if (!empty($extRef) && isset($orders[$extRef])) {
    $targetOrderId = $extRef;
}

// B) Se não veio na externalReference, busca no campo description ou nos pedidos pendentes
if (!$targetOrderId) {
    $description = $payment['description'] ?? '';
    if (preg_match('/HZ-\d+/', $description, $matches)) {
        if (isset($orders[$matches[0]])) {
            $targetOrderId = $matches[0];
        }
    }
}

// C) Fallback inteligente: se ainda não encontrou, associa ao pedido PENDING mais recente com valor correspondente
if (!$targetOrderId) {
    foreach (array_reverse($orders, true) as $id => $order) {
        if (($order['status'] ?? '') === 'PENDING') {
            $orderVal = (float)($order['offerPrice'] ?? 0);
            if (abs($orderVal - $paymentValue) < 0.5) {
                $targetOrderId = $id;
                break;
            }
        }
    }
}

// 5. ATUALIZA O STATUS DO PEDIDO PARA PAID
if ($targetOrderId && isset($orders[$targetOrderId])) {
    $orders[$targetOrderId]['status'] = 'PAID';
    $orders[$targetOrderId]['paidAt'] = date('c');
    $orders[$targetOrderId]['paymentDetails'] = [
        'paymentId'   => $paymentId,
        'billingType' => $billingType,
        'value'       => $paymentValue,
        'event'       => $event
    ];

    file_put_contents($dbFile, json_encode($orders, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
}

// Responde com HTTP 200 imediatamente como exigido pelo Asaas
http_response_code(200);
echo json_encode([
    'received' => true,
    'orderId'  => $targetOrderId,
    'status'   => 'PAID'
]);
