BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 25e35d6217de

CREATE TABLE api_key (
    id BIGSERIAL NOT NULL, 
    api_key VARCHAR NOT NULL, 
    tenant VARCHAR NOT NULL, 
    va_account VARCHAR NOT NULL, 
    is_active BOOLEAN DEFAULT true, 
    is_delete BOOLEAN DEFAULT false, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE TABLE atom_va_reconcile (
    id BIGSERIAL NOT NULL, 
    transactions JSON, 
    total_txn BIGINT, 
    total_amount FLOAT, 
    time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE TABLE atom_va_transaction (
    id BIGSERIAL NOT NULL, 
    bank_account_customer VARCHAR NOT NULL, 
    bank_account_receiver VARCHAR NOT NULL, 
    bill_id VARCHAR NOT NULL, 
    amount FLOAT NOT NULL, 
    callback_url VARCHAR, 
    customer_name VARCHAR NOT NULL, 
    customer_id BIGINT NOT NULL, 
    va_account_customer VARCHAR NOT NULL, 
    va_account_receiver VARCHAR NOT NULL, 
    va_partner VARCHAR NOT NULL, 
    is_reconcile BOOLEAN, 
    status VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE TABLE audit_log (
    id BIGSERIAL NOT NULL, 
    action_name VARCHAR, 
    description VARCHAR, 
    created_by VARCHAR, 
    event_time VARCHAR, 
    request_data JSON, 
    response_data JSON, 
    header_data JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE TABLE bank (
    id BIGSERIAL NOT NULL, 
    name VARCHAR, 
    bic VARCHAR, 
    full_name VARCHAR, 
    bank_code VARCHAR, 
    swift_code VARCHAR, 
    logo_url VARCHAR, 
    va_from_bank BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE TABLE atom_va_account (
    id BIGSERIAL NOT NULL, 
    bank_account_no VARCHAR NOT NULL, 
    bank_id BIGINT, 
    first_name VARCHAR, 
    last_name VARCHAR, 
    partner VARCHAR NOT NULL, 
    va_type VARCHAR NOT NULL, 
    va_partner VARCHAR NOT NULL, 
    account_no VARCHAR, 
    callback_url VARCHAR, 
    client_id BIGINT, 
    saving_id BIGINT, 
    va_account_no VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(bank_id) REFERENCES bank (id)
);

CREATE TABLE bank_account (
    id BIGSERIAL NOT NULL, 
    full_name VARCHAR, 
    address VARCHAR, 
    phone VARCHAR, 
    email VARCHAR, 
    identification_no VARCHAR NOT NULL, 
    birthday DATE DEFAULT now(), 
    bank_id BIGINT NOT NULL, 
    bank_code VARCHAR, 
    balance FLOAT DEFAULT 50000, 
    account_no VARCHAR NOT NULL, 
    expire_at DATE, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(bank_id) REFERENCES bank (id)
);

CREATE TABLE bank_transaction (
    id BIGSERIAL NOT NULL, 
    bank_account_customer BIGINT NOT NULL, 
    bank_account_receiver BIGINT NOT NULL, 
    bill_id VARCHAR NOT NULL, 
    callback_url VARCHAR NOT NULL, 
    status VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    amount FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(bank_account_customer) REFERENCES bank_account (id), 
    FOREIGN KEY(bank_account_receiver) REFERENCES bank_account (id)
);

CREATE TABLE bank_va_account (
    id BIGSERIAL NOT NULL, 
    bank_account BIGINT NOT NULL, 
    va_account_no VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(bank_account) REFERENCES bank_account (id)
);

INSERT INTO alembic_version (version_num) VALUES ('25e35d6217de') RETURNING alembic_version.version_num;

-- Running upgrade 25e35d6217de -> 4c615e8d38ee

ALTER TABLE bank ADD COLUMN callbank_url VARCHAR;

UPDATE alembic_version SET version_num='4c615e8d38ee' WHERE alembic_version.version_num = '25e35d6217de';

-- Running upgrade 4c615e8d38ee -> 1e93bd41ae64

ALTER TABLE atom_va_transaction ADD COLUMN partner VARCHAR NOT NULL;

UPDATE alembic_version SET version_num='1e93bd41ae64' WHERE alembic_version.version_num = '4c615e8d38ee';

-- Running upgrade 1e93bd41ae64 -> c204e4030524

CREATE TABLE industry (
    id BIGSERIAL NOT NULL, 
    code VARCHAR, 
    name VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

UPDATE alembic_version SET version_num='c204e4030524' WHERE alembic_version.version_num = '1e93bd41ae64';

-- Running upgrade c204e4030524 -> fcd2b46431a0

ALTER TABLE atom_va_account ADD COLUMN parent_va VARCHAR;

ALTER TABLE atom_va_account DROP COLUMN va_partner;

UPDATE alembic_version SET version_num='fcd2b46431a0' WHERE alembic_version.version_num = 'c204e4030524';

COMMIT;

