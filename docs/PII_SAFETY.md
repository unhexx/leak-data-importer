# PII Safety Strategy

This document outlines the Personally Identifiable Information (PII) classification and handling strategy for the leak-data-importer project.

## PII Classification

### HIGH RISK - Requires Maximum Protection
| Field | Description | Examples | Handling |
|-------|------------|----------|----------|
| passport | Russian domestic passport | 45 06 123456 | Mask in logs, encrypt at rest |
| snils | Insurance account number | 123-456-789 01 | Mask in logs, encrypt at rest |
| inn | Tax identification | 1234567890 | Mask in logs, encrypt at rest |
| foreign_passport | International passport | AB1234567 | Mask in logs, encrypt at rest |

### MEDIUM RISK - Requires Caution
| Field | Description | Examples | Handling |
|-------|------------|----------|----------|
| phone | Phone numbers | +79161234567 | May appear in logs |
| email | Email addresses | user@mail.ru | May appear in logs |
| birth_date | Date of birth | 1985-03-15 | Generally safe in aggregates |

### LOW RISK - Generally Safe
| Field | Description | Examples | Handling |
|-------|------------|----------|----------|
| fio | Full name | Иванов Иван Иванович | Safe for display |
| address | Physical address | г. Москва, ул. Ленина 1 | Safe in reports |
| vehicle | Vehicle info | Ваз 2114 | Safe in reports |

## PII Safety Rules

### 1. Logging
- NEVER log: passport, snils, inn, full document numbers
- MAY log: partially masked (****1234) for debugging
- NEVER log foreign_passport full number

### 2. Exports
- Neo4j export: Use masking for sensitive fields
- JSON/CSV exports: Apply redaction by default
- UI display: Show only last 4 characters masked

### 3. Debug Output
- No PII in stack traces
- No PII in error messages sent to external services
- No PII in metrics/telemetry

## Redaction Utilities

From `leak_data_importer.utils.redaction`:

```python
from leak_data_importer.utils.redaction import redact_passport, redact_snils, redact_inn

# Example usage
passport = "45 06 123456"
safe_passport = redact_passport(passport)  # "** ** *456"

snils = "123-456-789 01"
safe_snils = redact_snils(snils)  # "***-***-** 01"

inn = "1234567890"
safe_inn = redact_inn(inn)  # "**********"
```

## Future Enhancements

1. Add automatic PII detection in logs
2. Add GDPR-style export with field selection
3. Add audit logging for data access
4. Add data retention policies
