DROP TABLE IF EXISTS comments CASCADE;
DROP TABLE IF EXISTS posts CASCADE;
DROP TABLE IF EXISTS mood_entries CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS resources CASCADE;
DROP TABLE IF EXISTS users CASCADE;


DROP FUNCTION IF EXISTS update_updated_at_column;

CREATE TABLE users (
id SERIAL PRIMARY KEY,
username VARCHAR(50) UNIQUE NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
password_hash TEXT NOT NULL, 
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

is_default_anonymous BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_users_email ON users (email);


CREATE TABLE posts (
id SERIAL PRIMARY KEY,

user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
title VARCHAR(255) NOT NULL,
content TEXT NOT NULL,
is_anonymous BOOLEAN DEFAULT FALSE, 
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_user_id ON posts (user_id);

CREATE INDEX idx_posts_created_at ON posts (created_at DESC);


CREATE TABLE comments (
id SERIAL PRIMARY KEY,

post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,

user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
content TEXT NOT NULL,
is_anonymous BOOLEAN DEFAULT FALSE,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_post_id ON comments (post_id);
CREATE INDEX idx_comments_user_id ON comments (user_id);


CREATE TABLE mood_entries (
id SERIAL PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
mood_score INTEGER NOT NULL CHECK (mood_score BETWEEN 1 AND 10), 
notes TEXT,
entry_date DATE DEFAULT CURRENT_DATE,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE UNIQUE INDEX uidx_moods_user_date ON mood_entries (user_id, entry_date);


CREATE TABLE chat_sessions (
id SERIAL PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
topic VARCHAR(100), 
session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
session_end TIMESTAMP WITH TIME ZONE,

full_log_content TEXT,

ai_summary TEXT
);

CREATE INDEX idx_chats_user_id ON chat_sessions (user_id);


CREATE TABLE resources (
id SERIAL PRIMARY KEY,
name VARCHAR(255) NOT NULL,
resource_type VARCHAR(50) NOT NULL, 
contact_info VARCHAR(255),
website_url VARCHAR(255),
description TEXT,
is_verified BOOLEAN DEFAULT FALSE, 
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_resources_type ON resources (resource_type);


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
NEW.updated_at = NOW();
RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_post_updated_at
BEFORE UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


INSERT INTO users (username, email, password_hash) VALUES
('admin_user', 'admin@sih.com', 'hashed_password_1'),
('anonymous_user_01', 'anon@sih.com', 'hashed_password_2');

INSERT INTO posts (user_id, title, content, is_anonymous) VALUES
(1, 'Welcome to the Community Forum', 'Let''s keep this space positive and supportive!', FALSE),
(2, 'Feeling low today, need advice.', 'I woke up and just couldn''t get out of bed. Does anyone else struggle with motivation?', TRUE);

INSERT INTO comments (post_id, user_id, content, is_anonymous) VALUES
(2, 1, 'It happens! Try a small win, like just drinking a glass of water. Sending good vibes!', FALSE);

INSERT INTO resources (name, resource_type, contact_info, website_url, is_verified) VALUES
('National Suicide Prevention Lifeline', 'Hotline', '1-800-273-8255', 'https://www.google.com/search?q=http://www.example.com/lifeline', TRUE),
('Local Mental Health Clinic', 'Therapist', 'clinic@example.com', 'https://www.google.com/search?q=http://www.example.com/clinic', TRUE);