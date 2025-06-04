from collections import defaultdict
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
from app.utils.navigation import preserve_back_url
from app.models.enums import ResidentRole
from app.models.enums import UserRole

from app.forms import RegisterForm, LoginForm, AdminAddressForm, InviteForm, ProfileForm

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

        if user:
            if user.is_blocked:
                flash("Ваш аккаунт заблокирован. Обратитесь к администратору.", "danger")
                return redirect(url_for("web.login"))

            if check_password_hash(user.password, password):
                token = create_access_token(identity=str(user.id))
                session["user_id"] = user.id
                session["token"] = token
                session["user_role"] = user.role.value
                current_app.logger.info(f"Пользователь вошёл: {user.email}")
                return redirect(url_for("web.addresses"))

        flash("Неверные учетные данные", "danger")

    return render_template("login.html", form=form)



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

        return redirect(url_for("web.addresses"))

    return render_template("join_address.html")


@web_bp.route("/address/<int:address_id>/residents")
@preserve_back_url()
def address_residents(address_id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    address = Address.query.get_or_404(address_id)
    residents = UserAddress.query.filter_by(address_id=address_id).join(User).all()

    user_id = session["user_id"]
    full_control = has_full_control(user_id, address_id)

    return render_template(
        "address_residents.html",
        address=address,
        residents=residents,
        user_role="ADMIN" if full_control else None,
        current_user_id=user_id,
        back_url=session.get("_back_url", url_for("web.addresses"))
    )


@web_bp.route("/resident/<int:resident_id>/update-role", methods=["POST"])
def update_resident_role(resident_id):
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    ua = UserAddress.query.get_or_404(resident_id)
    address_id = ua.address_id

    if not has_full_control(session["user_id"], address_id):
        flash("Недостаточно прав", "danger")
        return redirect(url_for("web.addresses"))

    new_role = request.form["role"]
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

    if not has_full_control(session["user_id"], address_id):
        flash("Недостаточно прав", "danger")
        return redirect(url_for("web.addresses"))

    # 💡 Разрешим даже удаление себя, если админ
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

    # 💡 Разрешить если админ
    if not (is_admin() or UserAddress.query.filter_by(user_id=current_user_id, address_id=address.id)
                                     .filter(UserAddress.role.in_([ResidentRole.OWNER, ResidentRole.RESIDENT]))
                                     .first()):
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
            return redirect(url_for("web.address_residents", address_id=address.id))
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
            return redirect(url_for("web.addresses"))

        ua = UserAddress(
            user_id=session["user_id"],
            address_id=invitation.address_id,
            role=ResidentRole.GUEST
        )
        invitation.used = True
        db.session.add(ua)
        db.session.commit()

        flash("Вы успешно присоединились", "success")
        return redirect(url_for("web.addresses"))

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
        return redirect(url_for("web.addresses"))

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
            return redirect(url_for("web.addresses", mode="all"))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Ошибка при создании адреса", "danger")
            logging.error(f"Ошибка создания адреса: {str(e)}")

    addresses = Address.query.all()
    return render_template("admin_dashboard.html", addresses=addresses, form=form)



@web_bp.route("/admin/users")
def admin_users():
    if session.get("user_role") != "ADMIN":
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web.addresses"))

    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role", "all")
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    PER_PAGE = 10

    query = User.query

    if search:
        query = query.filter(User.email.ilike(f"%{search}%") | User.name.ilike(f"%{search}%"))

    if role_filter != "all":
        role_value = UserRole.ADMIN if role_filter == "admin" else UserRole.USER
        query = query.filter(User.role == role_value)

    if status_filter != "all":
        if status_filter == "blocked":
            query = query.filter(User.is_blocked == True)
        elif status_filter == "active":
            query = query.filter((User.is_blocked == False) | (User.is_blocked.is_(None)))

    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    users = pagination.items

    return render_template("admin_users.html",
                           users=users,
                           pagination=pagination,
                           search=search,
                           role_filter=role_filter,
                           status_filter=status_filter)


@web_bp.route("/admin/user/<int:user_id>/toggle-block")
def admin_toggle_user_block(user_id):
    if session.get("user_role") != "ADMIN":
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web.addresses"))

    user = User.query.get_or_404(user_id)
    user.is_blocked = not getattr(user, "is_blocked", False)

    try:
        db.session.commit()
        status = "заблокирован" if user.is_blocked else "разблокирован"
        flash(f"Пользователь {user.email} {status}", "info")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка блокировки: {str(e)}")
        flash("Ошибка блокировки", "danger")

    return redirect(url_for("web.admin_users"))


@web_bp.route("/admin/user/<int:user_id>/toggle-admin")
def admin_toggle_user_admin(user_id):
    if session.get("user_role") != "ADMIN":
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web.addresses"))


    user = User.query.get_or_404(user_id)

    user.role = UserRole.USER if user.role == UserRole.ADMIN else UserRole.ADMIN

    try:
        db.session.commit()
        flash(f"Пользователю {user.email} назначена роль: {user.role.name}", "info")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка назначения роли: {str(e)}")
        flash("Ошибка при смене роли", "danger")

    return redirect(url_for("web.admin_users"))


@web_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    user = User.query.get_or_404(session["user_id"])
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data

        if form.password.data:
            user.password = generate_password_hash(form.password.data)

        try:
            db.session.commit()
            flash("Профиль обновлён", "success")
            logging.info(f"Пользователь {user.id} обновил профиль")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Ошибка при обновлении профиля", "danger")
            logging.error(f"Ошибка обновления профиля: {str(e)}")

        return redirect(url_for("web.profile"))

    return render_template("profile.html", form=form)


@web_bp.route("/addresses")
def addresses():
    if "user_id" not in session:
        return redirect(url_for("web.login"))

    is_admin_mode = request.args.get("mode") == "all" and is_admin()

    user_id = session["user_id"]
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    filter_type = request.args.get("filter", "all")

    # Базовый запрос
    if is_admin_mode:
        query = Address.query
    else:
        user_addresses = UserAddress.query.filter_by(user_id=user_id).all()
        address_ids = [ua.address_id for ua in user_addresses]
        query = Address.query.filter(Address.id.in_(address_ids))
    user_ownership_ids = set(
        ua.address_id for ua in UserAddress.query.filter_by(user_id=user_id, role=ResidentRole.OWNER).all()
    )
    if search:
        query = query.filter(
            Address.street.ilike(f"%{search}%") |
            Address.building_number.ilike(f"%{search}%") |
            Address.unit_number.ilike(f"%{search}%")
        )

    addresses = query.all()

    # Подсчёт ролей
    from collections import defaultdict
    role_counts = defaultdict(lambda: {"OWNER": 0, "RESIDENT": 0, "GUEST": 0})
    for addr in addresses:
        for ua in addr.residents:
            role_counts[addr.id][ua.role.name] += 1

    # Фильтрация
    def passes_filter(address):
        rc = role_counts[address.id]
        if filter_type == "no_owner":
            return rc["OWNER"] == 0
        elif filter_type == "no_resident":
            return rc["RESIDENT"] == 0
        elif filter_type == "no_guest":
            return rc["GUEST"] == 0
        return True

    filtered = list(filter(passes_filter, addresses))

    # Пагинация
    PER_PAGE = 10
    total = len(filtered)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_items = filtered[start:end]

    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page

        def iter_pages(self):
            return range(1, self.pages + 1)

        @property
        def has_prev(self): return self.page > 1
        @property
        def has_next(self): return self.page < self.pages
        @property
        def prev_num(self): return self.page - 1
        @property
        def next_num(self): return self.page + 1

    pagination = Pagination(page, PER_PAGE, total)

    return render_template(
        "addresses.html",
        addresses=page_items,
        role_counts=role_counts,
        pagination=pagination,
        search=search,
        filter_type=filter_type,
        is_admin=is_admin_mode,
        user_ownership_ids=user_ownership_ids
    )


def has_full_control(user_id, address_id):
    from app.models.user import UserRole
    user_role = session.get("user_role")

    if user_role == UserRole.ADMIN.value:
        return True

    user_address = UserAddress.query.filter_by(user_id=user_id, address_id=address_id).first()
    return user_address and user_address.role.name == "OWNER"

@web_bp.route("/address/<int:address_id>/delete", methods=["POST"])
def delete_address(address_id):
    if not is_admin():
        abort(403)

    address = Address.query.get_or_404(address_id)

    # Удалим сначала связи
    UserAddress.query.filter_by(address_id=address_id).delete()
    Invitation.query.filter_by(address_id=address_id).delete()

    # Потом сам адрес
    db.session.delete(address)
    db.session.commit()

    flash("Адрес удалён.", "success")
    return redirect(url_for("web.addresses", mode="all"))
