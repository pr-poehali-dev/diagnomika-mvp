CREATE TABLE IF NOT EXISTS t_p13645480_diagnomika_mvp.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS t_p13645480_diagnomika_mvp.characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES t_p13645480_diagnomika_mvp.users(id),
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    soul TEXT NOT NULL,
    soul_level INT NOT NULL DEFAULT 50,
    mind TEXT NOT NULL,
    mind_level INT NOT NULL DEFAULT 50,
    body TEXT NOT NULL,
    body_level INT NOT NULL DEFAULT 50,
    strength TEXT NOT NULL,
    need TEXT NOT NULL,
    story TEXT NOT NULL,
    image_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS t_p13645480_diagnomika_mvp.daily_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES t_p13645480_diagnomika_mvp.users(id),
    task_date DATE NOT NULL DEFAULT CURRENT_DATE,
    task_text TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, task_date)
);

CREATE TABLE IF NOT EXISTS t_p13645480_diagnomika_mvp.journey (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES t_p13645480_diagnomika_mvp.users(id),
    day_number INT NOT NULL,
    title TEXT NOT NULL,
    entry_text TEXT NOT NULL,
    task_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
