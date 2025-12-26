
import sqlalchemy
from databases import Database

DATABASE_URL = "postgresql://user:password@localhost/dbname"

database = Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

inventory = sqlalchemy.Table(
    "inventory",
    metadata,
    sqlalchemy.Column("serial_number", sqlalchemy.String(50), primary_key=True),
    sqlalchemy.Column("passcode", sqlalchemy.String(12), nullable=False),
    sqlalchemy.Column("device_secret", sqlalchemy.String(64), nullable=False),
    sqlalchemy.Column("is_claimed", sqlalchemy.Boolean, default=False),
)

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID, primary_key=True, server_default=sqlalchemy.text("gen_random_uuid()")),
    sqlalchemy.Column("email", sqlalchemy.String(255), unique=True, nullable=False),
    sqlalchemy.Column("password_hash", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("stripe_customer_id", sqlalchemy.String(100)),
)

devices = sqlalchemy.Table(
    "devices",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID, primary_key=True, server_default=sqlalchemy.text("gen_random_uuid()")),
    sqlalchemy.Column("serial_number", sqlalchemy.String(50), sqlalchemy.ForeignKey("inventory.serial_number")),
    sqlalchemy.Column("user_id", sqlalchemy.dialects.postgresql.UUID, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("last_seen_at", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("activated_at", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("prepaid_expiry", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=True),
)

rules = sqlalchemy.Table(
    "rules",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.dialects.postgresql.UUID, primary_key=True, server_default=sqlalchemy.text("gen_random_uuid()")),
    sqlalchemy.Column("user_id", sqlalchemy.dialects.postgresql.UUID, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("threshold_hours", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("email_list", sqlalchemy.Text),
    sqlalchemy.Column("scope", sqlalchemy.String(20)),
)

alert_state = sqlalchemy.Table(
    "alert_state",
    metadata,
    sqlalchemy.Column("rule_id", sqlalchemy.dialects.postgresql.UUID, sqlalchemy.ForeignKey("rules.id"), primary_key=True),
    sqlalchemy.Column("device_id", sqlalchemy.dialects.postgresql.UUID, sqlalchemy.ForeignKey("devices.id"), primary_key=True),
    sqlalchemy.Column("last_triggered_at", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("is_resolved", sqlalchemy.Boolean, default=True),
)


engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)
