# app/commands.py
import click
from flask.cli import with_appcontext
from app.main.extensions import db
from app.models import User

@click.command("create-superuser")
@with_appcontext
def create_superuser():
    admin_email = "admin@example.com"
    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        click.echo("⚠️ Админ уже существует.")
        return
    admin = User(
        name="Админ",
        email=admin_email,
        role="ADMIN",
        password="scrypt:32768:8:1$EcndYJWiC62uN3Sd$2c76a063eab4efad90ef87df1a4163534c011d55bb02609cc848d2cb60f3b8dd3843d9f04e70f073b794a9f19f9b49447d09cc81681cf3fb1126bee7d0bec9c9"  # 🔐 Лучше хэшировать или брать из переменной окружения
    )
    db.session.add(admin)
    db.session.commit()
    click.echo("✅ Суперпользователь создан: admin@example.com / admin")
#TODO сделать пароль по нормальному