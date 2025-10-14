# JSON-схемы для интеллектуальной системы обучения AI GOST

## 1. Метаданные документа с проектной привязкой
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DocumentMetadata",
  "type": "object",
  "properties": {
    "documentId": { "type": "string" },
    "projectId": { "type": "string" },
    "projectName": { "type": "string" },
    "detectedType": { 
      "type": "string", 
      "enum": ["pdf", "image", "dwg", "smeta_arp", "smeta_gsfx", "normative", "unknown"] 
    },
    "sourceFileName": { "type": "string" },
    "sourceMime": { "type": "string" },
    "pages": { "type": "integer", "minimum": 0 },
    "language": { "type": "string" },
    "learningStatus": { 
      "type": "string", 
      "enum": ["pending", "processing", "learned", "failed"] 
    },
    "ingestedAt": { "type": "string", "format": "date-time" },
    "learnedAt": { "type": "string", "format": "date-time" }
  },
  "required": ["documentId", "projectId", "detectedType", "sourceFileName", "ingestedAt"]
}
```

## 2. Проект (основная единица работы)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Project",
  "type": "object",
  "properties": {
    "projectId": { "type": "string" },
    "projectName": { "type": "string" },
    "projectType": { 
      "type": "string", 
      "enum": ["substation", "canopy", "building", "infrastructure", "other"] 
    },
    "description": { "type": "string" },
    "status": { 
      "type": "string", 
      "enum": ["active", "completed", "archived"] 
    },
    "createdAt": { "type": "string", "format": "date-time" },
    "updatedAt": { "type": "string", "format": "date-time" },
    "documentsCount": { "type": "integer", "minimum": 0 },
    "learningProgress": { "type": "number", "minimum": 0, "maximum": 100 }
  },
  "required": ["projectId", "projectName", "projectType", "status", "createdAt"]
}
```

## 3. Текстовый запрос пользователя
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UserQuery",
  "type": "object",
  "properties": {
    "queryId": { "type": "string" },
    "userId": { "type": "string" },
    "projectId": { "type": "string" },
    "queryText": { "type": "string" },
    "queryType": { 
      "type": "string", 
      "enum": ["data_extraction", "analog_search", "calculation", "report", "other"] 
    },
    "context": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "status": { 
      "type": "string", 
      "enum": ["pending", "processing", "completed", "failed"] 
    },
    "response": { "type": "string" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
  },
  "required": ["queryId", "userId", "projectId", "queryText", "timestamp"]
}
```

## 4. База знаний (извлеченные данные)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "KnowledgeBase",
  "type": "object",
  "properties": {
    "knowledgeId": { "type": "string" },
    "projectId": { "type": "string" },
    "documentId": { "type": "string" },
    "dataType": { 
      "type": "string", 
      "enum": ["table", "text", "number", "date", "reference"] 
    },
    "content": { "type": "object" },
    "metadata": {
      "type": "object",
      "properties": {
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "source": { "type": "string" },
        "extractedAt": { "type": "string", "format": "date-time" }
      }
    },
    "tags": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["knowledgeId", "projectId", "dataType", "content"]
}
```

## 5. Структурированные табличные данные (для Excel)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StructuredTable",
  "type": "object",
  "properties": {
    "tableId": { "type": "string" },
    "projectId": { "type": "string" },
    "tableName": { "type": "string" },
    "tableType": { 
      "type": "string", 
      "enum": ["estimate", "specification", "schedule", "other"] 
    },
    "columns": { 
      "type": "array", 
      "items": { 
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "type": { "type": "string" },
          "format": { "type": "string" }
        }
      }
    },
    "rows": {
      "type": "array",
      "items": { "type": "array", "items": { "type": ["string", "number", "boolean", "null"] } }
    },
    "excelFormat": {
      "type": "object",
      "properties": {
        "sheetName": { "type": "string" },
        "headerRow": { "type": "integer" },
        "dataStartRow": { "type": "integer" }
      }
    }
  },
  "required": ["tableId", "projectId", "columns", "rows"]
}
```

## 6. Смета (упрощённая модель для ARP/GSFX)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Estimate",
  "type": "object",
  "properties": {
    "estimateId": { "type": "string" },
    "projectId": { "type": "string" },
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
          "section": { "type": "string" },
          "gostReference": { "type": "string" }
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
    },
    "excelExport": {
      "type": "object",
      "properties": {
        "fileName": { "type": "string" },
        "sheetName": { "type": "string" },
        "exportedAt": { "type": "string", "format": "date-time" }
      }
    }
  },
  "required": ["estimateId", "projectId", "items", "totals"]
}
```

## 7. Нормативная база (ГОСТы и стандарты)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NormativeDocument",
  "type": "object",
  "properties": {
    "normativeId": { "type": "string" },
    "documentType": { 
      "type": "string", 
      "enum": ["gost", "snip", "sp", "other"] 
    },
    "documentNumber": { "type": "string" },
    "title": { "type": "string" },
    "year": { "type": "integer" },
    "status": { 
      "type": "string", 
      "enum": ["active", "replaced", "cancelled"] 
    },
    "content": { "type": "string" },
    "keywords": { "type": "array", "items": { "type": "string" } },
    "learningStatus": { 
      "type": "string", 
      "enum": ["pending", "processing", "learned", "failed"] 
    },
    "ingestedAt": { "type": "string", "format": "date-time" }
  },
  "required": ["normativeId", "documentType", "documentNumber", "title", "status"]
}
```

## 8. Ответ системы на запрос
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SystemResponse",
  "type": "object",
  "properties": {
    "responseId": { "type": "string" },
    "queryId": { "type": "string" },
    "responseType": { 
      "type": "string", 
      "enum": ["text", "table", "excel", "error"] 
    },
    "content": { "type": "object" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "sources": { 
      "type": "array", 
      "items": { 
        "type": "object",
        "properties": {
          "documentId": { "type": "string" },
          "projectId": { "type": "string" },
          "relevance": { "type": "number", "minimum": 0, "maximum": 1 }
        }
      }
    },
    "excelFile": {
      "type": "object",
      "properties": {
        "fileName": { "type": "string" },
        "filePath": { "type": "string" },
        "fileSize": { "type": "integer" }
      }
    },
    "timestamp": { "type": "string", "format": "date-time" },
    "processingTime": { "type": "number" }
  },
  "required": ["responseId", "queryId", "responseType", "content", "timestamp"]
}
```

## 9. Пользователь системы
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SystemUser",
  "type": "object",
  "properties": {
    "userId": { "type": "string" },
    "userName": { "type": "string" },
    "userRole": { 
      "type": "string", 
      "enum": ["teacher", "user", "admin"] 
    },
    "email": { "type": "string", "format": "email" },
    "projects": { "type": "array", "items": { "type": "string" } },
    "permissions": {
      "type": "object",
      "properties": {
        "canTeach": { "type": "boolean" },
        "canQuery": { "type": "boolean" },
        "canExport": { "type": "boolean" },
        "canManageProjects": { "type": "boolean" }
      }
    },
    "createdAt": { "type": "string", "format": "date-time" },
    "lastActive": { "type": "string", "format": "date-time" }
  },
  "required": ["userId", "userName", "userRole", "email"]
}
```

---

**Примечание**: Схемы адаптированы под новую концепцию интеллектуальной системы обучения с проектно-ориентированной работой и текстовыми запросами. Все схемы включают поля для проектной привязки и статуса обучения системы.

