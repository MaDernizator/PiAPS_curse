from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.user import User
from app.models.address import Address
from app.models.user_address import UserAddress
from app.main.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models.enums import ResidentRole
from app.models.invitation import Invitation
from flask import abort
from flask import current_app

from app.forms import RegisterForm, LoginForm, AdminAddressForm, InviteForm


web_bp = Blueprint("web", __name__)

import logging


# logging.basicConfig(
#     filename='app.log',
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] %(message)s'
# )

def is_admin():
    from app.models.user import UserRole
    return session.get("user_role") == UserRole.ADMIN.value


@web_bp.route("/")
def index():
    return redirect(url_for("web.login"))


from app.forms import RegisterForm

@web_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        name = form.name.data

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Пользователь с таким email уже существует", "danger")
            return redirect(url_for("web.register"))

        hashed = generate_password_hash(password)

        try:
            user = User(name=name, email=email, password=hashed)
            db.session.add(user)
            db.session.commit()
            logging.info(f"Зарегистрирован новый пользователь: {email}")
            flash("Регистрация прошла успешно", "success")
            return redirect(url_for("web.login"))
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Ошибка регистрации: {str(e)}")
            flash("Ошибка при регистрации", "danger")

    return render_template("register.html", form=form)



@web_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            token = create_access_token(identity=str(user.id))
            session["user_id"] = user.id
            session["token"] = token
            session["user_role"] = user.role.value
            current_app.logger.info(f"Пользователь вошёл: {user.email}")
            return redirect(url_for("web.dashboard"))

        flash("Неверные учетные данные", "danger")

    return render_template("login.html", form=form)


@web_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("web.login"))
    user_id = session["user_id"]
    addresses = UserAddress.query.filter_by(user_id=user_id).all()
    return render_template("dashboard.html", addresses=addresses)


@web_bp.route("/join-address", methods=["GET", "POST"])
def join_address():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    if request.method == "POST":
        code = request.form["code"]
        from app.models.address import Address
        from app.models.user_address import UserAddress, ResidentRole
        from app.main.extensions import db

        try:
            address = Address.query.filter_by(owner_code=code).first()

            if not address:
                flash("Адрес с таким кодом не найден", "danger")
                return redirect(url_for("web.join_address"))

            if address.residents:
                flash("Адрес уже привязан к другому владельцу", "danger")
                return redirect(url_for("web.join_address"))

            address.owner_code = f"USED_{address.owner_code}"

            user_address = UserAddress(
                user_id=session["user_id"],
                address_id=address.id,
                role=ResidentRole.OWNER
            )

            try:
                db.session.add(address)
                db.session.add(user_address)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error(f"Ошибка при присоединении к адресу: {str(e)}")
                flash("Произошла ошибка при присоединении", "danger")

            flash("Вы успешно стали владельцем адреса", "success")
            logging.info(f"Пользователь {session['user_id']} стал владельцем адреса {address.id}")

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Ошибка при присоединении к адресу: {str(e)}")
            flash("Произошла ошибка при присоединении", "danger")

        return redirect(url_for("web.dashboard"))

    return render_template("join_address.html")


@web_bp.route("/address/<int:address_id>/residents")
def address_residents(address_id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    address = Address.query.get_or_404(address_id)

    residents = UserAddress.query.filter_by(address_id=address_id).join(User).all()

    # получаем роль текущего пользователя
    current_user_id = session["user_id"]
    current_resident = UserAddress.query.filter_by(
        user_id=current_user_id,
        address_id=address_id
    ).first()

    return render_template(
        "address_residents.html",
        address=address,
        residents=residents,
        user_role=current_resident.role.name,
        current_user_id=current_user_id
    )


@web_bp.route("/resident/<int:resident_id>/update-role", methods=["POST"])
def update_resident_role(resident_id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    ua = UserAddress.query.get_or_404(resident_id)
    new_role = request.form["role"]

    address_id = ua.address_id

    # проверка, что текущий пользователь — OWNER
    current = UserAddress.query.filter_by(
        user_id=session["user_id"],
        address_id=address_id
    ).first()
    if not current or current.role.name != "OWNER":
        flash("Недостаточно прав", "danger")
        return redirect(url_for("web.dashboard"))

    ua.role = ResidentRole[new_role]
    db.session.commit()

    flash("Роль обновлена", "success")
    return redirect(url_for("web.address_residents", address_id=address_id))


@web_bp.route("/resident/<int:resident_id>/remove", methods=["POST"])
def remove_resident(resident_id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    ua = UserAddress.query.get_or_404(resident_id)
    address_id = ua.address_id

    current = UserAddress.query.filter_by(
        user_id=session["user_id"],
        address_id=address_id
    ).first()
    if not current or current.role.name != "OWNER":
        flash("Недостаточно прав", "danger")
        return redirect(url_for("web.dashboard"))

    if ua.user_id == session["user_id"]:
        flash("Нельзя удалить самого себя", "warning")
        return redirect(url_for("web.dashboard"))

    db.session.delete(ua)
    db.session.commit()
    flash("Жилец удалён", "info")
    return redirect(url_for("web.address_residents", address_id=address_id))


@web_bp.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("web.login"))


@web_bp.route("/address/<int:address_id>/invite", methods=["GET", "POST"])
def invite_user(address_id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    address = Address.query.get_or_404(address_id)
    current_user_id = session["user_id"]

    ua = UserAddress.query.filter_by(user_id=current_user_id, address_id=address.id).first()
    if not ua or ua.role not in [ResidentRole.OWNER, ResidentRole.RESIDENT]:
        abort(403)

    form = InviteForm()
    if form.validate_on_submit():
        code = uuid.uuid4().hex
        invitation = Invitation(
            email=form.email.data,
            address_id=address.id,
            code=code,
            created_at=datetime.utcnow(),
            used=False
        )

        try:
            db.session.add(invitation)
            db.session.commit()
            logging.info(f"Пользователь {form.email.data} приглашён к адресу {address.id}")
            flash("Приглашение отправлено", "success")
            return redirect(url_for("web.dashboard"))
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Ошибка при приглашении: {str(e)}")
            flash("Ошибка при приглашении", "danger")

    return render_template("invite_user.html", address=address, form=form)


@web_bp.route("/accept-invitation", methods=["GET", "POST"])
def accept_invitation():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    if request.method == "POST":
        code = request.form["code"]
        invitation = Invitation.query.filter_by(code=code, used=False).first()

        if not invitation:
            flash("Приглашение не найдено или уже использовано", "danger")
            return redirect(url_for("web.accept_invitation"))

        # проверка: уже добавлен?
        exists = UserAddress.query.filter_by(
            user_id=session["user_id"],
            address_id=invitation.address_id
        ).first()
        if exists:
            flash("Вы уже добавлены к этому адресу", "warning")
            return redirect(url_for("web.dashboard"))

        ua = UserAddress(
            user_id=session["user_id"],
            address_id=invitation.address_id,
            role=ResidentRole.GUEST
        )
        invitation.used = True
        db.session.add(ua)
        db.session.commit()

        flash("Вы успешно присоединились", "success")
        return redirect(url_for("web.dashboard"))

    return render_template("accept_invitation.html")


@web_bp.route("/invitation/<int:id>/decline", methods=["POST"])
def decline_invitation(id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    invitation = Invitation.query.get_or_404(id)

    user = User.query.get(session["user_id"])
    if invitation.email != user.email:
        abort(403)

    try:
        db.session.delete(invitation)
        db.session.commit()
        flash("Приглашение отклонено", "info")
        logging.info(f"Пользователь {session['user_id']} отклонил приглашение {id}")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Ошибка при отклонении приглашения {id}: {str(e)}")
        flash("Ошибка при отклонении приглашения", "danger")

    return redirect(url_for("web.my_invitations"))


@web_bp.route("/my-invitations")
def my_invitations():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    user = User.query.get(session["user_id"])

    # Найти приглашения, которые совпадают по email и не использованы
    invites = Invitation.query.filter_by(email=user.email, used=False).all()

    return render_template("my_invitations.html", invites=invites)


@web_bp.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if session.get("user_role") != "ADMIN":
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web.dashboard"))

    form = AdminAddressForm()
    if form.validate_on_submit():
        address = Address(
            street=form.street.data,
            building_number=form.building.data,
            unit_number=form.unit.data,
            owner_code=form.code.data
        )
        try:
            db.session.add(address)
            db.session.commit()
            flash("Адрес создан", "success")
            logging.info(f"Админ создал адрес: {form.street.data}, {form.building.data}, {form.unit.data}")
            return redirect(url_for("web.admin_dashboard"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Ошибка при создании адреса", "danger")
            logging.error(f"Ошибка создания адреса: {str(e)}")

    addresses = Address.query.all()
    return render_template("admin_dashboard.html", addresses=addresses, form=form)


# TODO отклонить приглошение
