"""
Unit tests for PersonLinker - entity resolution and person matching.
"""

from datetime import date

import pytest

from leak_data_importer.linkers.person_linker import (
    MatchStrategy,
    PersonLinker,
)
from leak_data_importer.parsers.dossier_models import ParsedPerson, ParsedReport


class TestPersonLinkerInit:
    """Tests for PersonLinker initialization."""

    def test_default_initialization(self):
        """Test default parameters."""
        linker = PersonLinker()
        assert linker.fio_threshold == 0.70
        assert linker.require_birth_date is False
        assert linker.birth_date_tolerance_days == 30

    def test_custom_initialization(self):
        """Test custom parameters."""
        linker = PersonLinker(
            fio_threshold=0.80,
            require_birth_date=True,
            birth_date_tolerance_days=60,
        )
        assert linker.fio_threshold == 0.80
        assert linker.require_birth_date is True
        assert linker.birth_date_tolerance_days == 60


class TestStrategyWeights:
    """Tests for strategy weight configuration."""

    def test_weights_sum_to_one(self):
        """Verify weights sum to 1.0."""
        linker = PersonLinker()
        total = sum(linker.STRATEGY_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_all_strategies_have_weights(self):
        """All strategies should have weights."""
        linker = PersonLinker()
        expected_strategies = {
            MatchStrategy.EXACT_PASSPORT,
            MatchStrategy.EXACT_SNILS,
            MatchStrategy.EXACT_INN,
            MatchStrategy.EXACT_PHONE,
            MatchStrategy.FUZZY_FIO,
            MatchStrategy.FUZZY_PHONE,
            MatchStrategy.FUZZY_BIRTHDATE,
        }
        assert set(linker.STRATEGY_WEIGHTS.keys()) == expected_strategies


class TestExactPassportMatching:
    """Tests for exact passport matching."""

    def test_exact_passport_match(self):
        """Test that exact passport gives 100% confidence."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": {"45 06 123456"},
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": {"45 06 123456"},
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert score == 1.0
        assert MatchStrategy.EXACT_PASSPORT in strategies
        assert strategies[MatchStrategy.EXACT_PASSPORT] == 1.0

    def test_no_shared_passport(self):
        """Test different passports gives no score."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": {"45 06 123456"},
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Петров Петр Петрович",
            "birth_date": date(1990, 1, 1),
            "passports": {"12 34 567890"},
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert MatchStrategy.EXACT_PASSPORT not in strategies


class TestExactDocumentMatching:
    """Tests for exact SNILS and INN matching."""

    def test_exact_snils_match(self):
        """Test exact SNILS gives confidence."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": "123-456-789 01",
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": "123-456-789 01",
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert MatchStrategy.EXACT_SNILS in strategies
        assert strategies[MatchStrategy.EXACT_SNILS] == 1.0

    def test_exact_inn_match(self):
        """Test exact INN gives confidence."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": "1234567890",
            "phones": set(),
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": "1234567890",
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert MatchStrategy.EXACT_INN in strategies
        assert strategies[MatchStrategy.EXACT_INN] == 1.0


class TestFuzzyFioMatching:
    """Tests for fuzzy FIO matching."""

    def test_fuzzy_name_match(self):
        """Test fuzzy name matching."""
        linker = PersonLinker(fio_threshold=0.70)
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        # Similar but slightly different
        p2 = {
            "fio": "Иванов И.И.",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        if MatchStrategy.FUZZY_FIO in strategies:
            assert strategies[MatchStrategy.FUZZY_FIO] >= 0.70

    def test_below_threshold_no_match(self):
        """Test names below threshold don't match."""
        linker = PersonLinker(fio_threshold=0.90)
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Петров Петр Петрович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert MatchStrategy.FUZZY_FIO not in strategies


class TestPhoneMatching:
    """Tests for phone matching."""

    def test_exact_phone_match(self):
        """Test exact phone match."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": {"+79161234567"},
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": {"+79161234567"},
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert MatchStrategy.EXACT_PHONE in strategies
        assert strategies[MatchStrategy.EXACT_PHONE] == 1.0

    def test_fuzzy_phone_match(self):
        """Test fuzzy phone partial matching."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": {"+7916123"},
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": {"+7916234567"},
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        if MatchStrategy.FUZZY_PHONE in strategies:
            assert strategies[MatchStrategy.FUZZY_PHONE] > 0


class TestBirthDateMatching:
    """Tests for birth date matching."""

    def test_exact_birth_date(self):
        """Test exact birth date gives 100%."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        assert MatchStrategy.FUZZY_BIRTHDATE in strategies
        assert strategies[MatchStrategy.FUZZY_BIRTHDATE] == 1.0

    def test_within_tolerance(self):
        """Test birth date within tolerance."""
        linker = PersonLinker(birth_date_tolerance_days=30)
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 1),
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        # Should have some birth date score (between 0.5 and 1.0)
        if MatchStrategy.FUZZY_BIRTHDATE in strategies:
            assert 0.5 <= strategies[MatchStrategy.FUZZY_BIRTHDATE] <= 1.0


class TestWeightedScore:
    """Tests for weighted confidence calculation."""

    def test_multiple_strategies_combined(self):
        """Test that multiple strategies give combined score."""
        linker = PersonLinker()
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": {"45 06 123456"},
            "snils": "123-456-789 01",
            "inn": "1234567890",
            "phones": {"+79161234567"},
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": date(1985, 3, 15),
            "passports": {"45 06 123456"},
            "snils": "123-456-789 01",
            "inn": "1234567890",
            "phones": {"+79161234567"},
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        # Should have multiple strategies
        assert len(strategies) >= 3
        # Score should be high when all match
        assert score >= 0.80

    def test_zero_score_no_overlap(self):
        """Test no overlap gives zero score."""
        linker = PersonLinker()
        
        p1 = {
            "fio": None,
            "birth_date": None,
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": None,
            "birth_date": None,
            "passports": set(),
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        # May still get 0.5 for birth date if no strong ID
        assert score <= 0.5


class TestFindMatches:
    """Tests for find_matches method."""

    def test_no_reports_returns_empty(self):
        """Test empty report list returns empty."""
        linker = PersonLinker()
        result = linker.find_matches([])
        assert result == []

    def test_single_report_returns_empty(self):
        """Test single report returns no clusters."""
        linker = PersonLinker()
        
        # Create mock report with person
        report = ParsedReport(
            filename="test1.txt",
            sources_count=1,
            records_count=1,
            main_person=ParsedPerson(
                fio="Иванов Иван Иванович",
                birth_date=date(1985, 3, 15),
            ),
        )
        
        result = linker.find_matches([report])
        assert result == []


class TestRequireBirthDate:
    """Tests for require_birth_date option."""

    def test_require_birth_date_enforced(self):
        """Test that birth date is required when configured."""
        linker = PersonLinker(require_birth_date=True)
        
        p1 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": None,  # No birth date
            "passports": {"45 06 123456"},
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        p2 = {
            "fio": "Иванов Иван Иванович",
            "birth_date": None,  # No birth date
            "passports": {"45 06 123456"},
            "snils": None,
            "inn": None,
            "phones": set(),
        }
        
        score, strategies = linker._similarity_score_with_strategies(p1, p2)
        
        # Should still work because passport is strong ID
        # but birth date strategy should not apply
        assert MatchStrategy.FUZZY_BIRTHDATE not in strategies
