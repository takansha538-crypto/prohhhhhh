import os
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from database.schema import (
    Application,
    BrandProfile,
    Brief,
    Connection,
    CreatorProfile,
    Follow,
    Message,
    Notification,
    PortfolioProject,
    Project,
    SavedCreator,
    Skill,
    AITool,
    Specialization,
    User,
    db,
)
from database.seed import seed_if_empty
from services import ai_service
from services.matching import rank_creators, score_creator_against_brief

load_dotenv()

PROJECT_STAGES = [
    "Discovery",
    "Brief",
    "Shortlist",
    "Connect",
    "Hire",
    "Production",
    "Review",
    "Delivery",
    "Completed",
]


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "creatorshub-hackathon-demo-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, "creatorshub.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Work around a pysqlite prepared-statement bug in Python 3.14 sqlite3 where
    # the cached insert statement is re-executed with stale parameters, causing
    # spurious UNIQUE constraint failures during flush.  We also disable SQLite
    # dialect-level insert…RETURNING for the same driver reason.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {
            "cached_statements": 0,
            "check_same_thread": False,
            "timeout": 30,
        },
    }
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    with app.app_context():
        # Disable insert…RETURNING on the SQLite dialect; Python 3.14's pysqlite
        # driver has an intermittent bug where the same prepared statement is
        # re-run with old bound parameters when RETURNING clauses are used.
        try:
            db.engine.dialect.insert_returning = False
        except Exception:
            pass
        db.create_all()
        seed_if_empty()

    @app.context_processor
    def inject_globals():
        user = g.get("user")
        unread = 0
        if user:
            unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        return {
            "current_user": user,
            "unread_count": unread,
            "ai_live": ai_service.ai_available(),
            "now": datetime.utcnow(),
        }

    @app.before_request
    def load_user():
        g.user = None
        uid = session.get("user_id")
        if uid:
            g.user = User.query.get(uid)

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not g.user:
                flash("Please sign in to continue.", "info")
                return redirect(url_for("login", next=request.path))
            return fn(*args, **kwargs)

        return wrapper

    def notify(user_id, title, body, link=""):
        db.session.add(Notification(user_id=user_id, title=title, body=body, link=link))

    def verification_badges(creator):
        items = []
        if creator.profile_verified:
            items.append(
                {
                    "level": 1,
                    "label": "Profile Verified",
                    "tip": "Identity, location, and professional details have been reviewed.",
                }
            )
        if creator.tools_verified:
            items.append(
                {
                    "level": 2,
                    "label": "AI Tools Verified",
                    "tip": "Declared tools and models were checked against the creator’s workflow notes.",
                }
            )
        if creator.workflow_verified:
            items.append(
                {
                    "level": 3,
                    "label": "Workflow Verified",
                    "tip": "Production steps, revision process, and licensing notes were reviewed.",
                }
            )
        if creator.portfolio_verified:
            items.append(
                {
                    "level": 4,
                    "label": "Portfolio Verified",
                    "tip": "Selected projects were reviewed for process evidence and commercial-use claims.",
                }
            )
        if creator.trusted:
            items.append(
                {
                    "level": 5,
                    "label": "Creator Trusted",
                    "tip": "Highest trust tier: repeated commercial delivery and complete verification.",
                }
            )
        return items

    def connection_status(a_id, b_id):
        c = Connection.query.filter(
            or_(
                (Connection.requester_id == a_id) & (Connection.addressee_id == b_id),
                (Connection.requester_id == b_id) & (Connection.addressee_id == a_id),
            )
        ).first()
        return c

    def profile_completion(creator):
        checks = [
            bool(creator.headline),
            bool(creator.bio),
            bool(creator.workflow),
            bool(creator.skills),
            bool(creator.tools),
            bool(creator.portfolio),
            bool(creator.commercial_use),
            bool(creator.user.avatar),
        ]
        return int(100 * sum(1 for c in checks if c) / len(checks))

    @app.route("/")
    def index():
        featured = (
            CreatorProfile.query.filter(CreatorProfile.verification_level >= 4)
            .order_by(CreatorProfile.profile_views.desc())
            .limit(6)
            .all()
        )
        work = (
            PortfolioProject.query.filter_by(featured=True)
            .order_by(PortfolioProject.id.desc())
            .limit(8)
            .all()
        )
        specs = Specialization.query.order_by(Specialization.name).all()
        trusted = CreatorProfile.query.filter_by(trusted=True).limit(4).all()
        return render_template(
            "index.html",
            featured=featured,
            work=work,
            specs=specs,
            trusted=trusted,
            badges_fn=verification_badges,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Those credentials were not recognized. Try a demo account below.", "error")
                return render_template("login.html")
            session["user_id"] = user.id
            flash(f"Welcome back, {user.name.split()[0]}.", "success")
            nxt = request.args.get("next") or url_for("dashboard")
            return redirect(nxt)
        return render_template("login.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            role = request.form.get("role") or "creator"
            if role not in ("creator", "brand"):
                role = "creator"
            if not name or not email or len(password) < 6:
                flash("Name, email, and a password of at least 6 characters are required.", "error")
                return render_template("signup.html")
            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists. Sign in instead.", "error")
                return render_template("signup.html")
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                avatar="/static/images/avatars/default.svg",
                location=request.form.get("location") or "",
            )
            db.session.add(user)
            db.session.flush()
            if role == "creator":
                slug = "-".join(name.lower().split()) + f"-{user.id}"
                db.session.add(
                    CreatorProfile(
                        user_id=user.id,
                        slug=slug,
                        headline=request.form.get("headline") or "AI-native creator",
                        bio="",
                        availability="Available",
                    )
                )
            else:
                company = request.form.get("company") or name
                slug = "-".join(company.lower().split()) + f"-{user.id}"
                db.session.add(
                    BrandProfile(
                        user_id=user.id,
                        slug=slug,
                        company=company,
                        about=request.form.get("about") or "",
                    )
                )
            db.session.commit()
            session["user_id"] = user.id
            flash("Account created. Complete your profile from the dashboard.", "success")
            return redirect(url_for("dashboard"))
        return render_template("signup.html")

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            flash(
                "If that email exists, a reset link would be sent. For the hackathon demo, use Demo as Brand or Demo as Creator.",
                "info",
            )
            return redirect(url_for("login"))
        return render_template("forgot.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You signed out.", "info")
        return redirect(url_for("index"))

    @app.route("/demo/brand")
    def demo_brand():
        user = User.query.filter_by(email="novaframe@creatorshub.test").first_or_404()
        session["user_id"] = user.id
        flash("Exploring as NovaFrame Studios (brand demo).", "success")
        return redirect(url_for("dashboard"))

    @app.route("/demo/creator")
    def demo_creator():
        user = User.query.filter_by(email="aria@creatorshub.test").first_or_404()
        session["user_id"] = user.id
        flash("Exploring as Aria Chen (creator demo).", "success")
        return redirect(url_for("dashboard"))

    @app.route("/discover")
    def discover():
        q = (request.args.get("q") or "").strip()
        skill = request.args.get("skill") or ""
        spec = request.args.get("spec") or ""
        tool = request.args.get("tool") or ""
        content = request.args.get("content") or ""
        avail = request.args.get("availability") or ""
        verify = request.args.get("verification") or ""
        experience = request.args.get("experience") or ""
        budget = request.args.get("budget") or ""
        sort = request.args.get("sort") or "relevance"

        query = CreatorProfile.query.join(User)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    User.name.ilike(like),
                    CreatorProfile.headline.ilike(like),
                    CreatorProfile.bio.ilike(like),
                    CreatorProfile.content_types.ilike(like),
                )
            )
        if skill:
            query = query.filter(CreatorProfile.skills.any(Skill.name == skill))
        if spec:
            query = query.filter(CreatorProfile.specializations.any(Specialization.name == spec))
        if tool:
            query = query.filter(CreatorProfile.tools.any(AITool.name == tool))
        if content:
            query = query.filter(CreatorProfile.content_types.ilike(f"%{content}%"))
        if avail:
            query = query.filter(CreatorProfile.availability == avail)
        if verify:
            try:
                query = query.filter(CreatorProfile.verification_level >= int(verify))
            except ValueError:
                pass
        if experience:
            try:
                query = query.filter(CreatorProfile.experience_years >= int(experience))
            except ValueError:
                pass
        if budget:
            try:
                cap = int(budget)
                query = query.filter(CreatorProfile.hourly_rate <= cap)
            except ValueError:
                pass

        if sort == "rating":
            query = query.order_by(CreatorProfile.rating.desc())
        elif sort == "views":
            query = query.order_by(CreatorProfile.profile_views.desc())
        elif sort == "rate_low":
            query = query.order_by(CreatorProfile.hourly_rate.asc())
        elif sort == "rate_high":
            query = query.order_by(CreatorProfile.hourly_rate.desc())
        else:
            query = query.order_by(CreatorProfile.verification_level.desc(), CreatorProfile.profile_views.desc())

        creators = query.all()
        active = {k: v for k, v in request.args.items() if v and k != "sort"}
        return render_template(
            "discover.html",
            creators=creators,
            skills=Skill.query.order_by(Skill.name).all(),
            tools=AITool.query.order_by(AITool.name).all(),
            specs=Specialization.query.order_by(Specialization.name).all(),
            content_types=sorted(
                {c for p in CreatorProfile.query.all() for c in (p.content_types or "").split(", ") if c}
            ),
            filters=request.args,
            active=active,
            badges_fn=verification_badges,
        )

    @app.route("/creators/<slug>")
    def creator_profile(slug):
        creator = CreatorProfile.query.filter_by(slug=slug).first_or_404()
        creator.profile_views += 1
        db.session.commit()
        saved = False
        conn = None
        following = False
        if g.user:
            saved = SavedCreator.query.filter_by(brand_user_id=g.user.id, creator_id=creator.id).first() is not None
            conn = connection_status(g.user.id, creator.user_id)
            following = (
                Follow.query.filter_by(follower_id=g.user.id, followed_id=creator.user_id).first() is not None
            )
        related = (
            CreatorProfile.query.filter(CreatorProfile.id != creator.id)
            .order_by(CreatorProfile.verification_level.desc())
            .limit(3)
            .all()
        )
        return render_template(
            "creator_profile.html",
            creator=creator,
            badges=verification_badges(creator),
            saved=saved,
            conn=conn,
            following=following,
            related=related,
            summary=ai_service.generate_creator_summary(creator),
            completion=profile_completion(creator),
        )

    @app.route("/portfolio/<int:pid>")
    def portfolio_detail(pid):
        project = PortfolioProject.query.get_or_404(pid)
        related = (
            PortfolioProject.query.filter(
                PortfolioProject.creator_id == project.creator_id,
                PortfolioProject.id != project.id,
            )
            .limit(4)
            .all()
        )
        return render_template("portfolio.html", project=project, related=related, badges_fn=verification_badges)

    @app.route("/briefs")
    def briefs():
        q = (request.args.get("q") or "").strip()
        content = request.args.get("content") or ""
        tool = request.args.get("tool") or ""
        skill = request.args.get("skill") or ""
        query = Brief.query.filter(Brief.status != "Closed")
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Brief.title.ilike(like), Brief.description.ilike(like), Brief.style.ilike(like)))
        if content:
            query = query.filter(Brief.content_type == content)
        if tool:
            query = query.filter(Brief.tools.any(AITool.name == tool))
        if skill:
            query = query.filter(Brief.skills.any(Skill.name == skill))
        items = query.order_by(Brief.created_at.desc()).all()
        return render_template(
            "briefs.html",
            briefs=items,
            skills=Skill.query.order_by(Skill.name).all(),
            tools=AITool.query.order_by(AITool.name).all(),
            types=sorted({b.content_type for b in Brief.query.all()}),
            filters=request.args,
        )

    @app.route("/briefs/create", methods=["GET", "POST"])
    @login_required
    def create_brief():
        if g.user.role != "brand" or not g.user.brand_profile:
            flash("Briefs are published by brand accounts. Switch to the brand demo to try this flow.", "info")
            return redirect(url_for("briefs"))
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            if not title:
                flash("A campaign title is required.", "error")
                return redirect(url_for("create_brief"))
            try:
                bmin = int(request.form.get("budget_min") or 0)
                bmax = int(request.form.get("budget_max") or 0)
                qty = int(request.form.get("quantity") or 1)
                revs = int(request.form.get("revisions") or 2)
            except ValueError:
                flash("Budget, quantity, and revisions must be numbers.", "error")
                return redirect(url_for("create_brief"))
            brief = Brief(
                brand=g.user.brand_profile,
                title=title,
                description=request.form.get("description") or "",
                content_type=request.form.get("content_type") or "Video",
                creative_goal=request.form.get("creative_goal") or "",
                style=request.form.get("style") or "",
                visual_direction=request.form.get("visual_direction") or "",
                ai_requirements=request.form.get("ai_requirements") or "",
                format=request.form.get("format") or "MP4",
                aspect_ratio=request.form.get("aspect_ratio") or "16:9",
                resolution=request.form.get("resolution") or "4K",
                quantity=qty,
                deadline=request.form.get("deadline") or "",
                budget_min=bmin,
                budget_max=bmax,
                commercial_use=request.form.get("commercial_use") or "",
                licensing=request.form.get("licensing") or "",
                revisions=revs,
                deliverables=request.form.get("deliverables") or "",
                reference_links=request.form.get("reference_links") or "",
                notes=request.form.get("notes") or "",
                ai_generated=request.form.get("ai_generated") == "1",
            )
            skill_names = request.form.getlist("skills")
            tool_names = request.form.getlist("tools")
            brief.skills = Skill.query.filter(Skill.name.in_(skill_names)).all() if skill_names else []
            brief.tools = AITool.query.filter(AITool.name.in_(tool_names)).all() if tool_names else []
            db.session.add(brief)
            db.session.commit()
            flash("Brief published. Recommended creators are ready.", "success")
            return redirect(url_for("brief_detail", bid=brief.id))
        return render_template(
            "create_brief.html",
            skills=Skill.query.order_by(Skill.name).all(),
            tools=AITool.query.order_by(AITool.name).all(),
        )

    @app.route("/api/ai-brief", methods=["POST"])
    @login_required
    def api_ai_brief():
        idea = (request.json or {}).get("idea") or request.form.get("idea") or ""
        data = ai_service.generate_brief_from_idea(idea)
        return jsonify(data)

    @app.route("/briefs/<int:bid>")
    def brief_detail(bid):
        brief = Brief.query.get_or_404(bid)
        ranked = rank_creators(CreatorProfile.query.all(), brief, limit=6)
        applied = False
        if g.user and g.user.creator_profile:
            applied = (
                Application.query.filter_by(brief_id=brief.id, creator_id=g.user.creator_profile.id).first()
                is not None
            )
        return render_template(
            "brief_detail.html",
            brief=brief,
            ranked=ranked,
            applied=applied,
            badges_fn=verification_badges,
        )

    @app.route("/briefs/<int:bid>/apply", methods=["GET", "POST"])
    @login_required
    def apply_brief(bid):
        brief = Brief.query.get_or_404(bid)
        if not g.user.creator_profile:
            flash("Only creator accounts can apply to briefs.", "info")
            return redirect(url_for("brief_detail", bid=bid))
        existing = Application.query.filter_by(
            brief_id=brief.id, creator_id=g.user.creator_profile.id
        ).first()
        if existing:
            flash("You have already applied to this brief.", "info")
            return redirect(url_for("brief_detail", bid=bid))
        if request.method == "POST":
            cover = (request.form.get("cover_message") or "").strip()
            if len(cover) < 20:
                flash("Please write a short cover message (at least 20 characters).", "error")
                return redirect(url_for("apply_brief", bid=bid))
            try:
                budget = int(request.form.get("proposed_budget") or 0)
            except ValueError:
                flash("Proposed budget must be a number.", "error")
                return redirect(url_for("apply_brief", bid=bid))
            appn = Application(
                brief=brief,
                creator=g.user.creator_profile,
                cover_message=cover,
                proposed_budget=budget,
                estimated_delivery=request.form.get("estimated_delivery") or "",
                status="Applied",
            )
            pids = request.form.getlist("portfolio")
            if pids:
                appn.portfolio_items = PortfolioProject.query.filter(
                    PortfolioProject.id.in_(pids),
                    PortfolioProject.creator_id == g.user.creator_profile.id,
                ).all()
            db.session.add(appn)
            notify(
                brief.brand.user_id,
                "New application",
                f"{g.user.name} applied to {brief.title}.",
                url_for("brief_detail", bid=brief.id),
            )
            db.session.commit()
            flash("Application submitted.", "success")
            return redirect(url_for("applications"))
        return render_template("apply.html", brief=brief, creator=g.user.creator_profile)

    @app.route("/applications")
    @login_required
    def applications():
        if g.user.role == "creator" and g.user.creator_profile:
            items = (
                Application.query.filter_by(creator_id=g.user.creator_profile.id)
                .order_by(Application.created_at.desc())
                .all()
            )
        elif g.user.role == "brand" and g.user.brand_profile:
            items = (
                Application.query.join(Brief)
                .filter(Brief.brand_id == g.user.brand_profile.id)
                .order_by(Application.created_at.desc())
                .all()
            )
        else:
            items = []
        return render_template("applications.html", applications=items)

    @app.route("/applications/<int:aid>/status", methods=["POST"])
    @login_required
    def application_status(aid):
        appn = Application.query.get_or_404(aid)
        if not g.user.brand_profile or appn.brief.brand_id != g.user.brand_profile.id:
            abort(403)
        status = request.form.get("status") or "Applied"
        if status not in ("Applied", "Shortlisted", "Interview", "Accepted", "Rejected", "Completed"):
            flash("Unknown status.", "error")
            return redirect(url_for("applications"))
        appn.status = status
        notify(
            appn.creator.user_id,
            f"Application {status.lower()}",
            f"Your application for {appn.brief.title} is now {status}.",
            url_for("applications"),
        )
        if status == "Accepted":
            existing = Project.query.filter_by(brief_id=appn.brief_id, creator_id=appn.creator_id).first()
            if not existing:
                db.session.add(
                    Project(
                        brief=appn.brief,
                        brand=appn.brief.brand,
                        creator=appn.creator,
                        title=appn.brief.title,
                        stage="Hire",
                        budget=appn.proposed_budget,
                    )
                )
            flash("Creator hired. A project workspace was opened.", "success")
        else:
            flash(f"Application marked {status}.", "success")
        db.session.commit()
        return redirect(request.referrer or url_for("applications"))

    @app.route("/connect/<int:uid>", methods=["POST"])
    @login_required
    def connect(uid):
        if uid == g.user.id:
            flash("You cannot connect with yourself.", "error")
            return redirect(request.referrer or url_for("discover"))
        other = User.query.get_or_404(uid)
        existing = connection_status(g.user.id, uid)
        if existing:
            if existing.status == "accepted":
                flash("You are already connected.", "info")
            elif existing.status == "pending":
                flash("A connection request is already pending.", "info")
            else:
                existing.status = "pending"
                existing.requester_id = g.user.id
                existing.addressee_id = uid
                db.session.commit()
                flash("Connection request sent.", "success")
            return redirect(request.referrer or url_for("connections"))
        db.session.add(Connection(requester_id=g.user.id, addressee_id=uid, status="pending"))
        notify(uid, "Connection request", f"{g.user.name} wants to connect.", url_for("connections"))
        db.session.commit()
        flash("Connection request sent.", "success")
        return redirect(request.referrer or url_for("connections"))

    @app.route("/connections")
    @login_required
    def connections():
        incoming = Connection.query.filter_by(addressee_id=g.user.id, status="pending").all()
        outgoing = Connection.query.filter_by(requester_id=g.user.id, status="pending").all()
        accepted = Connection.query.filter(
            Connection.status == "accepted",
            or_(Connection.requester_id == g.user.id, Connection.addressee_id == g.user.id),
        ).all()
        following = Follow.query.filter_by(follower_id=g.user.id).all()
        return render_template(
            "connections.html",
            incoming=incoming,
            outgoing=outgoing,
            accepted=accepted,
            following=following,
        )

    @app.route("/connections/<int:cid>/<action>", methods=["POST"])
    @login_required
    def connection_action(cid, action):
        conn = Connection.query.get_or_404(cid)
        if action == "accept" and conn.addressee_id == g.user.id:
            conn.status = "accepted"
            notify(conn.requester_id, "Connection accepted", f"{g.user.name} accepted your request.", "/connections")
            flash("Connection accepted.", "success")
        elif action == "reject" and conn.addressee_id == g.user.id:
            conn.status = "rejected"
            flash("Request declined.", "info")
        elif action == "remove" and g.user.id in (conn.requester_id, conn.addressee_id):
            db.session.delete(conn)
            flash("Connection removed.", "info")
        else:
            abort(403)
        db.session.commit()
        return redirect(url_for("connections"))

    @app.route("/follow/<int:uid>", methods=["POST"])
    @login_required
    def follow(uid):
        if uid == g.user.id:
            return redirect(request.referrer or url_for("discover"))
        existing = Follow.query.filter_by(follower_id=g.user.id, followed_id=uid).first()
        if existing:
            db.session.delete(existing)
            flash("Unfollowed.", "info")
        else:
            db.session.add(Follow(follower_id=g.user.id, followed_id=uid))
            flash("Following.", "success")
        db.session.commit()
        return redirect(request.referrer or url_for("connections"))

    @app.route("/save/<int:cid>", methods=["POST"])
    @login_required
    def save_creator(cid):
        if g.user.role != "brand":
            flash("Saved lists are for brand accounts.", "info")
            return redirect(request.referrer or url_for("discover"))
        creator = CreatorProfile.query.get_or_404(cid)
        existing = SavedCreator.query.filter_by(brand_user_id=g.user.id, creator_id=cid).first()
        if existing:
            db.session.delete(existing)
            flash("Removed from saved creators.", "info")
        else:
            db.session.add(SavedCreator(brand_user_id=g.user.id, creator_id=cid))
            flash("Creator saved.", "success")
        db.session.commit()
        return redirect(request.referrer or url_for("creator_profile", slug=creator.slug))

    @app.route("/saved")
    @login_required
    def saved():
        items = SavedCreator.query.filter_by(brand_user_id=g.user.id).order_by(SavedCreator.created_at.desc()).all()
        return render_template("saved.html", items=items, badges_fn=verification_badges)

    @app.route("/messages")
    @login_required
    def messages():
        uid = g.user.id
        rows = Message.query.filter(or_(Message.sender_id == uid, Message.recipient_id == uid)).order_by(
            Message.created_at.desc()
        ).all()
        partners = {}
        for m in rows:
            other_id = m.recipient_id if m.sender_id == uid else m.sender_id
            if other_id not in partners:
                partners[other_id] = m
        people = [(User.query.get(i), last) for i, last in partners.items()]
        return render_template("messages.html", people=people, active=None, thread=[])

    @app.route("/messages/<int:uid>", methods=["GET", "POST"])
    @login_required
    def conversation(uid):
        other = User.query.get_or_404(uid)
        if request.method == "POST":
            body = (request.form.get("body") or "").strip()
            if not body:
                flash("Write a message before sending.", "error")
                return redirect(url_for("conversation", uid=uid))
            db.session.add(
                Message(
                    sender_id=g.user.id,
                    recipient_id=uid,
                    body=body,
                    attachment_type=request.form.get("attachment_type") or "",
                    attachment_id=int(request.form.get("attachment_id") or 0) or None,
                )
            )
            notify(uid, "New message", f"{g.user.name} sent you a message.", url_for("conversation", uid=g.user.id))
            db.session.commit()
            flash("Message sent.", "success")
            return redirect(url_for("conversation", uid=uid))
        thread = (
            Message.query.filter(
                or_(
                    (Message.sender_id == g.user.id) & (Message.recipient_id == uid),
                    (Message.sender_id == uid) & (Message.recipient_id == g.user.id),
                )
            )
            .order_by(Message.created_at.asc())
            .all()
        )
        for m in thread:
            if m.recipient_id == g.user.id:
                m.is_read = True
        db.session.commit()
        rows = Message.query.filter(
            or_(Message.sender_id == g.user.id, Message.recipient_id == g.user.id)
        ).order_by(Message.created_at.desc()).all()
        partners = {}
        for m in rows:
            other_id = m.recipient_id if m.sender_id == g.user.id else m.sender_id
            if other_id not in partners:
                partners[other_id] = m
        people = [(User.query.get(i), last) for i, last in partners.items()]
        attach_port = []
        attach_briefs = []
        if g.user.creator_profile:
            attach_port = g.user.creator_profile.portfolio
        if g.user.brand_profile:
            attach_briefs = g.user.brand_profile.briefs
        return render_template(
            "messages.html",
            people=people,
            active=other,
            thread=thread,
            attach_port=attach_port,
            attach_briefs=attach_briefs,
        )

    @app.route("/hire/<int:cid>", methods=["GET", "POST"])
    @login_required
    def hire(cid):
        creator = CreatorProfile.query.get_or_404(cid)
        if g.user.role != "brand" or not g.user.brand_profile:
            flash("Hiring is available on brand accounts. Use Demo as Brand to try it.", "info")
            return redirect(url_for("creator_profile", slug=creator.slug))
        if request.method == "POST":
            title = (request.form.get("title") or f"Engagement with {creator.user.name}").strip()
            try:
                budget = int(request.form.get("budget") or 0)
            except ValueError:
                budget = 0
            project = Project(
                brand=g.user.brand_profile,
                creator=creator,
                title=title,
                stage="Hire",
                budget=budget,
                notes=request.form.get("notes") or "",
                brief_id=int(request.form.get("brief_id") or 0) or None,
            )
            db.session.add(project)
            notify(
                creator.user_id,
                "You were hired",
                f"{g.user.brand_profile.company} hired you for {title}.",
                "/projects",
            )
            db.session.commit()
            flash("Creator hired. Project created.", "success")
            return redirect(url_for("project_detail", pid=project.id))
        return render_template("hire.html", creator=creator)

    @app.route("/projects")
    @login_required
    def projects():
        if g.user.role == "brand" and g.user.brand_profile:
            items = Project.query.filter_by(brand_id=g.user.brand_profile.id).all()
        elif g.user.role == "creator" and g.user.creator_profile:
            items = Project.query.filter_by(creator_id=g.user.creator_profile.id).all()
        else:
            items = []
        return render_template("projects.html", projects=items, stages=PROJECT_STAGES)

    @app.route("/projects/<int:pid>", methods=["GET", "POST"])
    @login_required
    def project_detail(pid):
        project = Project.query.get_or_404(pid)
        allowed = {project.brand.user_id, project.creator.user_id}
        if g.user.id not in allowed:
            abort(403)
        if request.method == "POST":
            stage = request.form.get("stage")
            if stage in PROJECT_STAGES:
                project.stage = stage
                db.session.commit()
                flash("Project stage updated.", "success")
            return redirect(url_for("project_detail", pid=pid))
        return render_template("project_detail.html", project=project, stages=PROJECT_STAGES)

    @app.route("/dashboard", methods=["GET", "POST"])
    @login_required
    def dashboard():
        if g.user.role == "creator" and g.user.creator_profile:
            c = g.user.creator_profile
            apps = Application.query.filter_by(creator_id=c.id).all()
            projs = Project.query.filter_by(creator_id=c.id).all()
            if request.method == "POST" and request.form.get("form") == "profile":
                c.headline = request.form.get("headline") or c.headline
                c.bio = request.form.get("bio") or c.bio
                c.workflow = request.form.get("workflow") or c.workflow
                c.availability = request.form.get("availability") or c.availability
                c.languages = request.form.get("languages") or c.languages
                c.commercial_use = request.form.get("commercial_use") or c.commercial_use
                c.content_types = request.form.get("content_types") or c.content_types
                try:
                    c.hourly_rate = int(request.form.get("hourly_rate") or c.hourly_rate)
                    c.project_rate_min = int(request.form.get("project_rate_min") or c.project_rate_min)
                    c.project_rate_max = int(request.form.get("project_rate_max") or c.project_rate_max)
                    c.experience_years = int(request.form.get("experience_years") or c.experience_years)
                except ValueError:
                    flash("Rates and experience must be numbers.", "error")
                    return redirect(url_for("dashboard"))
                g.user.location = request.form.get("location") or g.user.location
                skill_names = request.form.getlist("skills")
                tool_names = request.form.getlist("tools")
                spec_names = request.form.getlist("specs")
                if skill_names:
                    c.skills = Skill.query.filter(Skill.name.in_(skill_names)).all()
                if tool_names:
                    c.tools = AITool.query.filter(AITool.name.in_(tool_names)).all()
                if spec_names:
                    c.specializations = Specialization.query.filter(Specialization.name.in_(spec_names)).all()
                db.session.commit()
                flash("Profile updated.", "success")
                return redirect(url_for("dashboard"))
            if request.method == "POST" and request.form.get("form") == "portfolio":
                title = (request.form.get("title") or "").strip()
                if not title:
                    flash("Project title is required.", "error")
                    return redirect(url_for("dashboard"))
                p = PortfolioProject(
                    creator=c,
                    title=title,
                    description=request.form.get("description") or "",
                    content_type=request.form.get("content_type") or "Video",
                    workflow=request.form.get("workflow") or "",
                    commercial_use=request.form.get("commercial_use") or "Commercial licensed",
                    license_info=request.form.get("license_info") or "",
                    aspect_ratio=request.form.get("aspect_ratio") or "16:9",
                    outcome=request.form.get("outcome") or "",
                    cover_image="/static/images/portfolio/default.svg",
                )
                db.session.add(p)
                db.session.commit()
                flash("Portfolio project added.", "success")
                return redirect(url_for("dashboard"))
            return render_template(
                "dashboard_creator.html",
                creator=c,
                badges=verification_badges(c),
                completion=profile_completion(c),
                applications=apps,
                projects=projs,
                skills=Skill.query.order_by(Skill.name).all(),
                tools=AITool.query.order_by(AITool.name).all(),
                specs=Specialization.query.order_by(Specialization.name).all(),
            )
        brand = g.user.brand_profile
        if not brand:
            flash("Complete signup as a brand or creator.", "info")
            return redirect(url_for("index"))
        my_briefs = Brief.query.filter_by(brand_id=brand.id).all()
        apps = Application.query.join(Brief).filter(Brief.brand_id == brand.id).all()
        projs = Project.query.filter_by(brand_id=brand.id).all()
        saved_items = SavedCreator.query.filter_by(brand_user_id=g.user.id).all()
        return render_template(
            "dashboard_brand.html",
            brand=brand,
            briefs=my_briefs,
            applications=apps,
            projects=projs,
            saved=saved_items,
            badges_fn=verification_badges,
        )

    @app.route("/notifications")
    @login_required
    def notifications():
        items = (
            Notification.query.filter_by(user_id=g.user.id)
            .order_by(Notification.created_at.desc())
            .all()
        )
        return render_template("notifications.html", items=items)

    @app.route("/notifications/read", methods=["POST"])
    @login_required
    def notifications_read():
        Notification.query.filter_by(user_id=g.user.id).update({"is_read": True})
        db.session.commit()
        return redirect(request.referrer or url_for("notifications"))

    @app.route("/notifications/partial")
    @login_required
    def notifications_partial():
        items = (
            Notification.query.filter_by(user_id=g.user.id)
            .order_by(Notification.created_at.desc())
            .limit(8)
            .all()
        )
        return render_template("_notifications.html", items=items)

    @app.route("/brands/<slug>")
    def brand_profile(slug):
        brand = BrandProfile.query.filter_by(slug=slug).first_or_404()
        return render_template("brand_profile.html", brand=brand)

    @app.route("/demo-guide")
    def demo_guide():
        return render_template("demo_guide.html")

    @app.route("/presentation")
    def presentation():
        return render_template("presentation.html")

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="That page is not on CreatorsHub."), 404

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, message="You do not have access to that."), 403

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html", code=500, message="Something went wrong. Try the demo accounts."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", host="127.0.0.1", port=5000)
