# Примеры JSON-схем для структурированных данных (черновик)

## 1. Метаданные документа (auto-detection)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DocumentMetadata",
  "type": "object",
  "properties": {
    "documentId": { "type": "string" },
    "detectedType": { "type": "string", "enum": ["pdf", "image", "dwg", "smeta_arp", "smeta_gsfx", "unknown"] },
    "sourceFileName": { "type": "string" },
    "sourceMime": { "type": "string" },
    "pages": { "type": "integer", "minimum": 0 },
    "language": { "type": "string" },
    "ingestedAt": { "type": "string", "format": "date-time" }
  },
  "required": ["documentId", "detectedType", "sourceFileName", "ingestedAt"]
}
```

## 2. Структурированные табличные данные (универсальная таблица)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StructuredTable",
  "type": "object",
  "properties": {
    "tableName": { "type": "string" },
    "columns": { "type": "array", "items": { "type": "string" } },
    "rows": {
      "type": "array",
      "items": { "type": "array", "items": { "type": ["string", "number", "boolean", "null"] } }
    }
  },
  "required": ["columns", "rows"]
}
```

## 3. Смета (упрощённая модель для ARP/GSFX)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Estimate",
  "type": "object",
  "properties": {
    "estimateId": { "type": "string" },
    "currency": { "type": "string", "default": "RUB" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": { "type": "string" },
          "name": { "type": "string" },
          "unit": { "type": "string" },
          "quantity": { "type": "number" },
          "price": { "type": "number" },
          "amount": { "type": "number" },
          "section": { "type": "string" }
        },
        "required": ["name", "quantity", "price", "amount"]
      }
    },
    "totals": {
      "type": "object",
      "properties": {
        "subtotal": { "type": "number" },
        "tax": { "type": "number" },
        "total": { "type": "number" }
      },
      "required": ["total"]
    }
  },
  "required": ["items", "totals"]
}
```

//TODO: Уточнить обязательные поля для смет ARP/GSFX и соответствие с форматами экспорта заказчика.

