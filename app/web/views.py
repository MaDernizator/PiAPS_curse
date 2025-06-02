from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from app.models.user import User
from app.models.address import Address
from app.models.user_address import UserAddress
from app.main.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models.enums import ResidentRole
from app.models.invitation import Invitation

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    return redirect(url_for("web.login"))


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Регистрация успешна!", "success")
        return redirect(url_for("web.login"))
    return render_template("register.html")


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            token = create_access_token(identity=str(user.id))
            session["user_id"] = user.id
            session["token"] = token
            return redirect(url_for("web.dashboard"))
        flash("Неверные учетные данные", "danger")
    return render_template("login.html")


@web_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("web.login"))
    user_id = session["user_id"]
    addresses = UserAddress.query.filter_by(user_id=user_id).all()
    return render_template("dashboard.html", addresses=addresses)


import uuid  # 👈 добавляем вверху


@web_bp.route("/create-address", methods=["GET", "POST"])
def create_address():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    if request.method == "POST":
        street = request.form["street"]
        building = request.form["building"]
        unit = request.form["unit"]

        # 👇 Генерируем owner_code
        owner_code = str(uuid.uuid4()).replace("-", "")[:12]  # 12 символов

        address = Address(
            street=street,
            building_number=building,
            unit_number=unit,
            owner_code=owner_code
        )
        db.session.add(address)
        db.session.commit()

        ua = UserAddress(
            user_id=session["user_id"],
            address_id=address.id,
            role=ResidentRole.OWNER
        )
        db.session.add(ua)
        db.session.commit()

        return redirect(url_for("web.dashboard"))

    return render_template("create_address.html")


@web_bp.route("/join-address", methods=["GET", "POST"])
def join_address():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    if request.method == "POST":
        from app.models.user_address import UserAddress
        from app.models.address import Address
        from app.models.enums import ResidentRole

        code = request.form["owner_code"]
        address = Address.query.filter_by(owner_code=code).first()

        if not address:
            flash("Неверный код владельца", "danger")
            return redirect(url_for("web.join_address"))

        exists = UserAddress.query.filter_by(
            user_id=session["user_id"],
            address_id=address.id
        ).first()

        if exists:
            flash("Вы уже привязаны к этому адресу", "warning")
            return redirect(url_for("web.dashboard"))

        ua = UserAddress(
            user_id=session["user_id"],
            address_id=address.id,
            role=ResidentRole.RESIDENT
        )
        db.session.add(ua)
        db.session.commit()

        flash("Вы присоединились к адресу", "success")
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

    # проверка владельца
    ua = UserAddress.query.filter_by(user_id=session["user_id"], address_id=address_id).first()
    if not ua or ua.role != ResidentRole.OWNER and ua.role != ResidentRole.RESIDENT:
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web.dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        code = str(uuid.uuid4()).replace("-", "")

        invitation = Invitation(
            email=email,
            address_id=address_id,
            code=code
        )
        db.session.add(invitation)
        db.session.commit()

        flash(f"Приглашение создано. Код: {code}", "success")
        # (опционально: email-отправка)
        return redirect(url_for("web.dashboard"))

    return render_template("invite_user.html")


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
            role=ResidentRole.RESIDENT
        )
        invitation.used = True
        db.session.add(ua)
        db.session.commit()

        flash("Вы успешно присоединились", "success")
        return redirect(url_for("web.dashboard"))

    return render_template("accept_invitation.html")


@web_bp.route("/my-invitations")
def my_invitations():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    user = User.query.get(session["user_id"])

    # Найти приглашения, которые совпадают по email и не использованы
    invites = Invitation.query.filter_by(email=user.email, used=False).all()

    return render_template("my_invitations.html", invites=invites)