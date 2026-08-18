CREATE TABLE people (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  primary_email VARCHAR(320) NULL,
  primary_phone VARCHAR(32) NULL,
  city_raw VARCHAR(120) NULL,
  city_canonical VARCHAR(120) NULL,
  experience_years DECIMAL(5, 2) NULL,
  current_ctc INT NULL,
  applied_date DATE NULL,
  gig_rate_amount INT NULL,
  gig_rate_period VARCHAR(20) NULL,
  gig_status VARCHAR(32) NULL,
  cb_verified BOOLEAN NULL,
  projects_completed INT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  INDEX ix_people_normalized_name (normalized_name),
  INDEX ix_people_city_canonical (city_canonical),
  INDEX ix_people_name_city (normalized_name, city_canonical)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE person_emails (
  id INT AUTO_INCREMENT PRIMARY KEY,
  person_id INT NOT NULL,
  email VARCHAR(320) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_person_emails_person FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE person_phones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  person_id INT NOT NULL,
  phone_e164 VARCHAR(32) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL,
  CONSTRAINT fk_person_phones_person FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE skills (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE person_skills (
  person_id INT NOT NULL,
  skill_id INT NOT NULL,
  PRIMARY KEY (person_id, skill_id),
  CONSTRAINT fk_person_skills_person FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
  CONSTRAINT fk_person_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE source_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  person_id INT NOT NULL,
  source_name VARCHAR(80) NOT NULL,
  source_row_number INT NOT NULL,
  match_strategy VARCHAR(80) NOT NULL,
  issue_notes TEXT NULL,
  raw_json TEXT NOT NULL,
  created_at DATETIME NOT NULL,
  UNIQUE KEY uq_source_row (source_name, source_row_number),
  CONSTRAINT fk_source_records_person FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE audio_submissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  person_id INT NULL,
  name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  phone_e164 VARCHAR(32) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  stored_filename VARCHAR(255) NOT NULL,
  storage_path VARCHAR(512) NOT NULL,
  content_type VARCHAR(120) NULL,
  duration_seconds FLOAT NULL,
  sample_rate_khz FLOAT NULL,
  sample_rate_hz INT NULL,
  bitrate_kbps FLOAT NULL,
  loudness_db FLOAT NULL,
  quality_estimate VARCHAR(32) NOT NULL,
  noise_estimate VARCHAR(80) NULL,
  analysis_notes TEXT NULL,
  created_at DATETIME NOT NULL,
  INDEX ix_audio_submissions_normalized_name (normalized_name),
  INDEX ix_audio_submissions_phone_e164 (phone_e164),
  CONSTRAINT fk_audio_submissions_person FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
