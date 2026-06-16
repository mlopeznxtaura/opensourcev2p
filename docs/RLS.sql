-- PostgreSQL Row-Level Security skeleton for production deployment.
-- Apply when migrating off SQLite.
ALTER TABLE records ENABLE ROW LEVEL SECURITY;
CREATE POLICY records_owner ON records
    USING (care_id = current_setting('app.care_id', true));
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_self ON users
    USING (care_id = current_setting('app.care_id', true));
