# Тесты утилит маскирования PII данных.
# Проверяют корректность работы функций redact_*.

from leak_data_importer.utils.redaction import (
    redact_passport,
    redact_snils,
    redact_inn,
    redact_phone,
    redact_email,
    redact_document,
    is_pii_safe,
)


class TestPassportRedaction:
    # Тесты маскирования паспорта.

    def test_passport_full(self):
        # Полный паспорт маскируется корректно.
        result = redact_passport("45 06 123456")
        assert result == "** ** 3456"

    def test_passport_no_spaces(self):
        # Паспорт без пробелов.
        result = redact_passport("4506123456")
        assert result == "** ** 3456"

    def test_passport_short(self):
        # Короткий паспорт.
        result = redact_passport("4506")
        assert result == "****"

    def test_passport_empty(self):
        # Пустой паспорт.
        result = redact_passport("")
        assert result == ""


class TestSnilsRedaction:
    # Тесты маскирования СНИЛС.

    def test_snils_full(self):
        # Полный СНИЛС маскируется корректно.
        result = redact_snils("123-456-789 01")
        assert result == "***-***-** 01"

    def test_snils_no_dashes(self):
        # СНИЛС без дефисов.
        result = redact_snils("12345678901")
        assert result == "***-***-** 01"

    def test_snils_empty(self):
        # Пустой СНИЛС.
        result = redact_snils("")
        assert result == ""


class TestInnRedaction:
    # Тесты маскирования ИНН.

    def test_inn_full(self):
        # Полный ИНН маскируется полностью.
        result = redact_inn("1234567890")
        assert result == "**********"

    def test_inn_short(self):
        # Короткий ИНН.
        result = redact_inn("1234")
        assert result == "****"

    def test_inn_empty(self):
        # Пустой ИНН.
        result = redact_inn("")
        assert result == ""


class TestPhoneRedaction:
    # Тесты маскирования телефона.

    def test_phone_full(self):
        # Полный телефон.
        result = redact_phone("+79161234567")
        assert result == "+79***4567"

    def test_phone_no_plus(self):
        # Телефон без +.
        result = redact_phone("89161234567")
        assert result == "+79***4567"

    def test_phone_empty(self):
        # Пустой телефон.
        result = redact_phone("")
        assert result == ""


class TestEmailRedaction:
    # Тесты маскирования email.

    def test_email_full(self):
        # Полный email.
        result = redact_email("user@mail.ru")
        assert result == "u***@mail.ru"

    def test_email_short_name(self):
        # Email с коротким именем.
        result = redact_email("a@domain.com")
        assert result == "*@domain.com"

    def test_email_no_at(self):
        # Email без @ обрабатывается универсально.
        result = redact_email("nodomain")
        assert "*" in result


class TestDocumentRedaction:
    # Тесты универсального маскирования.

    def test_document_short(self):
        # Короткий документ.
        result = redact_document("AB")
        assert result == "AB"

    def test_document_full(self):
        # Полный документ.
        result = redact_document("AB123456")
        assert result == "AB**56"


class TestPiiSafety:
    # Тесты проверки безопасности PII.

    def test_safe_already_masked(self):
        # Уже маскированные данные безопасны.
        assert is_pii_safe("** ** 3456")

    def test_safe_clean(self):
        # Чистые данные небезопасны.
        assert not is_pii_safe("45 06 123456", "passport")
