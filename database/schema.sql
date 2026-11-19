-- ==========================================================================
-- EMORPHOSIS — Estrutura Inicial MySQL para Hostinger
-- ==========================================================================

CREATE TABLE IF NOT EXISTS marcas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(100) NOT NULL UNIQUE,
  nome VARCHAR(150) NOT NULL,
  categoria VARCHAR(100) DEFAULT NULL,
  instagram_handle VARCHAR(100) DEFAULT NULL,
  site_url VARCHAR(255) DEFAULT NULL,
  imagem_url VARCHAR(255) DEFAULT NULL,
  descricao TEXT DEFAULT NULL,
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inscritos_drops (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(190) NOT NULL,
  marca_slug VARCHAR(100) DEFAULT NULL,
  criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_email_marca (email, marca_slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
