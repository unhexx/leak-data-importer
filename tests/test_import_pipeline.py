"""
Интеграционные тесты для импорта данных.

Эти тесты проверяют полный цикл импорта:
- Чтение файлов различных форматов
- П парсинг в структурированные записи
- П статистика и метрики качества
- Генерация графов сущностей
"""

from pathlib import Path

import pytest

from leak_data_importer.importers.txt_report import TxtReportImporter


class TestTxtReportImporterBasics:
    """Тесты базовой функциональности TxtReportImporter."""

    @pytest.fixture
    def sample_file(self) -> Path:
        """Путь к тестовому файлу."""
        return Path(__file__).parent / "fixtures" / "sample_report.txt"

    def test_importer_initialization(self, sample_file: Path):
        """Тест инициализации импортера."""
        importer = TxtReportImporter(sample_file)
        assert importer.source == sample_file
        assert importer.name == "txt_report"

    def test_importer_can_handle(self, sample_file: Path):
        """Тест определения поддерживаемых форматов."""
        assert TxtReportImporter.can_handle(sample_file)

    def test_iter_records_yields_results(self, sample_file: Path):
        """Тест получения записей через итератор."""
        importer = TxtReportImporter(sample_file)
        records = list(importer.iter_records())
        
        # Должны получить хотя бы одну запись
        assert len(records) > 0
        
        # Проверяем структуру первой записи
        first = records[0]
        assert first.full_name is not None
        assert first.source_file is not None

    def test_parse_with_stats(self, sample_file: Path):
        """Тест метода parse_with_stats()."""
        importer = TxtReportImporter(sample_file)
        records, stats = importer.parse_with_stats()
        
        # Проверяем записи
        assert len(records) > 0
        
        # Проверяем статистику
        assert stats.total_blocks > 0
        assert stats.records_extracted > 0
        assert stats.files_processed
        assert isinstance(stats.by_strategy, dict)


class TestImportPipeline:
    """Тесты сквозного пайплайна импорта."""

    @pytest.fixture
    def sample_file(self) -> Path:
        """Путь к тестовому файлу."""
        return Path(__file__).parent / "fixtures" / "sample_report.txt"

    def test_full_pipeline_iteration(self, sample_file: Path):
        """Тест полного цикла итерации по записям."""
        importer = TxtReportImporter(sample_file)
        
        # Итерируемся по записям
        record_count = 0
        for record in importer.iter_records():
            record_count += 1
            
            # Каждая запись должна иметь source_block_id
            assert record.source_block_id is not None
            
            # Если есть ФИО, проверяем формат
            if record.full_name:
                assert len(record.full_name) > 0
        
        assert record_count > 0

    def test_full_pipeline_with_stats(self, sample_file: Path):
        """Тест полного цикла со статистикой."""
        importer = TxtReportImporter(sample_file)
        records, stats = importer.parse_with_stats()
        
        # Проверяем конфиденцию
        for record in records:
            if record.confidence is not None:
                assert 0.0 <= record.confidence <= 1.0
        
        # Проверяем стратегию парсинга
        assert all(r.parsing_strategy is not None for r in records)

    def test_graph_mode(self, sample_file: Path):
        """Тест генерации графового представления."""
        importer = TxtReportImporter(sample_file)
        result = importer.parse_to_graph()
        
        # Проверяем структуру результата
        assert result.graph is not None
        assert result.flat_records is not None
        assert result.stats is not None
        
        # Проверяем метаданные графа
        assert result.graph.metadata is not None
        assert "parser" in result.graph.metadata
        
        # Проверяем сущности и связи
        assert len(result.graph.entities) > 0
        assert len(result.graph.relationships) >= 0


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.fixture
    def sample_file(self) -> Path:
        """Путь к тестовому файлу."""
        return Path(__file__).parent / "fixtures" / "sample_report.txt"

    def test_nonexistent_file(self):
        """Тест обработки несуществующего файла."""
        importer = TxtReportImporter("/non/existent/file.txt")
        
        with pytest.raises(FileNotFoundError):
            list(importer.iter_records())

    def test_empty_file_handling(self, tmp_path: Path):
        """Тест обработки пустого файла."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")
        
        importer = TxtReportImporter(empty_file)
        records = list(importer.iter_records())
        
        # Пустой файл не должен давать записей
        assert len(records) == 0

    def test_custom_options(self, sample_file: Path):
        """Тест передачи пользовательских опций."""
        importer = TxtReportImporter(
            sample_file,
            encoding="utf-8",
            min_block_len=30
        )
        
        assert importer.encoding == "utf-8"
        assert importer.min_block_len == 30


class TestDataIntegrity:
    """Тесты целостности данных."""

    @pytest.fixture
    def sample_file(self) -> Path:
        """Путь к тестовому файлу."""
        return Path(__file__).parent / "fixtures" / "sample_report.txt"

    def test_record_deduplication(self, sample_file: Path):
        """Тест дедупликации данных в записях."""
        importer = TxtReportImporter(sample_file)
        records, _ = importer.parse_with_stats()
        
        for record in records:
            # Телефоны должны быть дедуплицированы
            if len(record.phones) > 1:
                assert len(record.phones) == len(set(record.phones))
            
            # Email должны быть дедуплицированы
            if len(record.emails) > 1:
                assert len(record.emails) == len(set(record.emails))

    def test_source_tracking(self, sample_file: Path):
        """Тест отслеживания источника данных."""
        importer = TxtReportImporter(sample_file)
        records, _ = importer.parse_with_stats()
        
        for record in records:
            # Каждая запись должна иметь идентификатор блока
            assert record.source_block_id is not None
            
            # Каждая запись должна ссылаться на файл
            assert record.source_file is not None
