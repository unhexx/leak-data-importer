-- =============================================
-- ПОЛНАЯ ТОЧНАЯ СХЕМА БД ДЛЯ ИМПОРТА ОТЧЁТОВ
-- (как указано в детальной спецификации)
-- =============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Enums
CREATE TYPE doc_type AS ENUM (
    'passport_rf', 'foreign_passport', 'snils', 'inn', 
    'oms_policy', 'driver_license', 'other'
);

CREATE TYPE address_type AS ENUM (
    'registration', 'actual', 'work', 'previous', 'birth_place', 'other'
);

CREATE TYPE connection_type AS ENUM (
    'parent', 'child', 'spouse', 'relative', 
    'travel_companion', 'flight_companion', 'address_cohabitant', 'other'
);

CREATE TYPE event_type AS ENUM (
    'border_crossing_in', 'border_crossing_out', 'flight', 'dtp', 'fssp_debt', 'other'
);

-- =============================================
-- CORE TABLES
-- =============================================

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    report_date TIMESTAMPTZ,
    sources_count INTEGER,
    records_count INTEGER,
    main_fio TEXT NOT NULL,
    main_birth_date DATE,
    raw_header JSONB,
    status TEXT DEFAULT 'imported',
    warnings JSONB DEFAULT '[]'::jsonb,
    created_by TEXT,
    CONSTRAINT uq_reports_filename UNIQUE (filename)
);

CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    fio TEXT NOT NULL,
    birth_date DATE,
    main_passport TEXT,
    main_snils TEXT,
    main_inn TEXT,
    main_phone TEXT,
    main_email TEXT,
    passport_count INTEGER DEFAULT 0,
    phone_count INTEGER DEFAULT 0,
    email_count INTEGER DEFAULT 0,
    address_count INTEGER DEFAULT 0,
    extra_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    doc_type doc_type NOT NULL,
    number TEXT NOT NULL,
    series TEXT,
    issue_date DATE,
    expiry_date DATE,
    issuer TEXT,
    issuer_code TEXT,
    status TEXT,
    birth_place TEXT,
    registration_address TEXT,
    extra JSONB DEFAULT '{}'::jsonb,
    source_section TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_documents_person ON documents(person_id);
CREATE INDEX idx_documents_number ON documents(number);
CREATE INDEX idx_documents_type ON documents(doc_type);

CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    address_type address_type NOT NULL,
    full_text TEXT NOT NULL,
    normalized JSONB,
    frequency INTEGER DEFAULT 1,
    source TEXT,
    extra JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_addresses_person ON addresses(person_id);
CREATE INDEX idx_addresses_full_text_gin ON addresses USING gin (full_text gin_trgm_ops);

CREATE TABLE employments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    employer_name TEXT,
    employer_inn TEXT,
    employer_ogrn TEXT,
    position TEXT,
    start_date DATE,
    end_date DATE,
    salary_annual NUMERIC(15,2),
    salary_monthly NUMERIC(15,2),
    source TEXT,
    extra JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE person_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    related_fio TEXT NOT NULL,
    related_birth_date DATE,
    connection_type connection_type NOT NULL,
    source TEXT,
    context JSONB,
    confidence REAL DEFAULT 0.8,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    gos_number TEXT,
    vin TEXT,
    make_model TEXT,
    year INTEGER,
    extra JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    event_type event_type NOT NULL,
    event_date TIMESTAMPTZ,
    flight_number TEXT,
    airline TEXT,
    departure TEXT,
    arrival TEXT,
    country TEXT,
    direction TEXT,
    passport_used TEXT,
    companion_fio TEXT,
    debt_amount NUMERIC(15,2),
    extra JSONB DEFAULT '{}'::jsonb,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE source_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    record_index INTEGER,
    data JSONB NOT NULL,
    raw_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_source_findings_person ON source_findings(person_id);
CREATE INDEX idx_source_findings_source ON source_findings(source_name);
CREATE INDEX idx_source_findings_data_gin ON source_findings USING gin (data);

-- =============================================
-- INDEXES & CONSTRAINTS
-- =============================================

CREATE INDEX idx_persons_fio_gin ON persons USING gin (fio gin_trgm_ops);
CREATE INDEX idx_persons_main_passport ON persons(main_passport);
CREATE INDEX idx_persons_main_snils ON persons(main_snils);
CREATE INDEX idx_persons_main_inn ON persons(main_inn);
CREATE INDEX idx_persons_main_phone ON persons(main_phone);

ALTER TABLE documents ADD CONSTRAINT uq_doc_per_report 
    UNIQUE (person_id, doc_type, number, report_id);

-- =============================================
-- VIEWS
-- =============================================

CREATE OR REPLACE VIEW v_active_documents AS
SELECT * FROM documents 
WHERE status = 'active' OR expiry_date IS NULL OR expiry_date > CURRENT_DATE;
