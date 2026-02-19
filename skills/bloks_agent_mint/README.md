# BLOKS Agent Mint API

Минимальный Python-скрипт для взаимодействия с BLOKS Agent Mint API.

## Описание

Скрипт реализует полный flow для минта агентов через BLOKS API:
1. Получение challenge (задача Proof of Work)
2. Решение PoW (подбор nonce для SHA-256 хеша)
3. Отправка решения для верификации
4. Минт агента

Опционально поддерживает whitelist-подпись через ed25519 (требует пакет `solders`).

## Установка

### Базовые зависимости
```bash
pip install -r requirements.txt
```

### Для поддержки whitelist-подписи (опционально)
```bash
pip install solders>=0.20.0
```

Или добавьте `solders` в `requirements.txt` и установите все зависимости.

## Использование

### Базовый минт (без whitelist)
```bash
python mint.py --wallet YOUR_WALLET_ADDRESS
```

### Минт с whitelist-подписью
```bash
python mint.py --wallet YOUR_WALLET_ADDRESS --private-key YOUR_PRIVATE_KEY_BASE58
```

### Пользовательский API endpoint
```bash
python mint.py --wallet YOUR_WALLET --base-url https://testnet.bloks.art
```

### Изменение интервала прогресса
```bash
python mint.py --wallet YOUR_WALLET --progress-interval 50000
```

## Параметры

- `--wallet` (обязательный): Адрес Solana кошелька (base58)
- `--base-url`: Базовый URL BLOKS API (по умолчанию: https://bloks.art)
- `--private-key`: Приватный ключ для whitelist-подписи (base58, опционально)
- `--progress-interval`: Интервал вывода прогресса в итерациях (по умолчанию: 100000)

## Пример вывода

```
==================================================
BLOKS Agent Mint API Client
==================================================
Wallet: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
Base URL: https://bloks.art
Whitelist signing: No

[1/4] Getting challenge for wallet: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
  Challenge received: id=abc123, target=0000
  Expires at: 2024-01-01T12:05:00Z
Starting PoW: prefix=xyz789, target=0000
Searching for nonce... (Ctrl+C to stop)
  Progress: 100,000 iterations, 1,250,000 ops/sec
  Progress: 200,000 iterations, 1,180,000 ops/sec
✓ PoW solved! nonce=2847392, hash=0000f3a29b...
  Time: 1.84s, iterations: 2847392

[2/4] Verifying solution...
  Verified! Token: eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...

[3/4] Minting agent...
  Mint response: {
  "success": true,
  "mint": "BAfyCISzQq...,
  "transaction": "4s7kSHoNG...,

==================================================
✓ Mint completed successfully!
==================================================
```

## Требования

- Python 3.7+
- `requests>=2.31.0`
- Опционально: `solders>=0.20.0` для whitelist-подписи

##Примечания

- Challenge имеет короткий срок действия (≈5 минут), поэтому PoW должен быть решен сразу после получения
- PoW может потребовать значительных вычислительных ресурсов в зависимости от сложности
- При ошибках API (429 Too Many Requests, 403 Forbidden, 400 Bad Request) выводится детализированная ошибка
- Whitelist-подпись опциональна и требует установки дополнительного пакета `solders`

## Структура проекта

```
skills/bloks_agent_mint/
├── mint.py           # Основной скрипт
├── requirements.txt  # Зависимости
└── README.md         # Документация
```