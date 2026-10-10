from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


creator_skills = db.Table(
    "creator_skills",
    db.Column("creator_id", db.Integer, db.ForeignKey("creator_profiles.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id"), primary_key=True),
)

creator_tools = db.Table(
    "creator_tools",
    db.Column("creator_id", db.Integer, db.ForeignKey("creator_profiles.id"), primary_key=True),
    db.Column("tool_id", db.Integer, db.ForeignKey("ai_tools.id"), primary_key=True),
)

creator_specs = db.Table(
    "creator_specializations",
    db.Column("creator_id", db.Integer, db.ForeignKey("creator_profiles.id"), primary_key=True),
    db.Column("spec_id", db.Integer, db.ForeignKey("specializations.id"), primary_key=True),
)

portfolio_skills = db.Table(
    "portfolio_skills",
    db.Column("project_id", db.Integer, db.ForeignKey("portfolio_projects.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id"), primary_key=True),
)

portfolio_tools = db.Table(
    "portfolio_tools",
    db.Column("project_id", db.Integer, db.ForeignKey("portfolio_projects.id"), primary_key=True),
    db.Column("tool_id", db.Integer, db.ForeignKey("ai_tools.id"), primary_key=True),
)

brief_skills = db.Table(
    "brief_skills",
    db.Column("brief_id", db.Integer, db.ForeignKey("briefs.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id"), primary_key=True),
)

brief_tools = db.Table(
    "brief_tools",
    db.Column("brief_id", db.Integer, db.ForeignKey("briefs.id"), primary_key=True),
    db.Column("tool_id", db.Integer, db.ForeignKey("ai_tools.id"), primary_key=True),
)

application_portfolio = db.Table(
    "application_portfolio",
    db.Column("application_id", db.Integer, db.ForeignKey("applications.id"), primary_key=True),
    db.Column("project_id", db.Integer, db.ForeignKey("portfolio_projects.id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # creator | brand
    avatar = db.Column(db.String(255), default="/static/images/avatars/default.svg")
    location = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_demo = db.Column(db.Boolean, default=False)

    creator_profile = db.relationship("CreatorProfile", back_populates="user", uselist=False)
    brand_profile = db.relationship("BrandProfile", back_populates="user", uselist=False)
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class AITool(db.Model):
    __tablename__ = "ai_tools"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    category = db.Column(db.String(80), default="Generative")


class Specialization(db.Model):
    __tablename__ = "specializations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)


class CreatorProfile(db.Model):
    __tablename__ = "creator_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    headline = db.Column(db.String(180), default="")
    bio = db.Column(db.Text, default="")
    workflow = db.Column(db.Text, default="")
    experience_years = db.Column(db.Integer, default=1)
    availability = db.Column(db.String(40), default="Available")  # Available | Limited | Booked
    languages = db.Column(db.String(180), default="English")
    hourly_rate = db.Column(db.Integer, default=80)
    project_rate_min = db.Column(db.Integer, default=1500)
    project_rate_max = db.Column(db.Integer, default=8000)
    commercial_use = db.Column(db.Text, default="")
    content_types = db.Column(db.String(255), default="Video")
    profile_views = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=4.8)
    review_count = db.Column(db.Integer, default=0)
    earnings_ytd = db.Column(db.Integer, default=0)
    completed_projects = db.Column(db.Integer, default=0)
    verification_level = db.Column(db.Integer, default=1)
    profile_verified = db.Column(db.Boolean, default=True)
    tools_verified = db.Column(db.Boolean, default=False)
    workflow_verified = db.Column(db.Boolean, default=False)
    portfolio_verified = db.Column(db.Boolean, default=False)
    trusted = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="creator_profile")
    skills = db.relationship("Skill", secondary=creator_skills, backref="creators")
    tools = db.relationship("AITool", secondary=creator_tools, backref="creators")
    specializations = db.relationship("Specialization", secondary=creator_specs, backref="creators")
    portfolio = db.relationship("PortfolioProject", back_populates="creator", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="creator", cascade="all, delete-orphan")


class BrandProfile(db.Model):
    __tablename__ = "brand_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    company = db.Column(db.String(160), nullable=False)
    industry = db.Column(db.String(80), default="Creative")
    about = db.Column(db.Text, default="")
    website = db.Column(db.String(180), default="")
    size = db.Column(db.String(40), default="11–50")

    user = db.relationship("User", back_populates="brand_profile")
    briefs = db.relationship("Brief", back_populates="brand", cascade="all, delete-orphan")


class PortfolioProject(db.Model):
    __tablename__ = "portfolio_projects"
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("creator_profiles.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, default="")
    content_type = db.Column(db.String(80), default="Video")
    workflow = db.Column(db.Text, default="")
    commercial_use = db.Column(db.String(80), default="Commercial licensed")
    license_info = db.Column(db.String(180), default="Exclusive campaign license")
    aspect_ratio = db.Column(db.String(20), default="16:9")
    outcome = db.Column(db.Text, default="")
    cover_image = db.Column(db.String(255), default="")
    verified = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("CreatorProfile", back_populates="portfolio")
    skills = db.relationship("Skill", secondary=portfolio_skills)
    tools = db.relationship("AITool", secondary=portfolio_tools)


class Brief(db.Model):
    __tablename__ = "briefs"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brand_profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    content_type = db.Column(db.String(80), default="Video")
    creative_goal = db.Column(db.String(200), default="")
    style = db.Column(db.String(160), default="")
    visual_direction = db.Column(db.Text, default="")
    ai_requirements = db.Column(db.Text, default="")
    format = db.Column(db.String(80), default="MP4")
    aspect_ratio = db.Column(db.String(20), default="16:9")
    resolution = db.Column(db.String(40), default="4K")
    quantity = db.Column(db.Integer, default=1)
    deadline = db.Column(db.String(40), default="")
    budget_min = db.Column(db.Integer, default=2000)
    budget_max = db.Column(db.Integer, default=8000)
    commercial_use = db.Column(db.String(160), default="Full commercial use")
    licensing = db.Column(db.String(160), default="Exclusive 12-month campaign license")
    revisions = db.Column(db.Integer, default=2)
    deliverables = db.Column(db.Text, default="")
    reference_links = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    status = db.Column(db.String(40), default="Open")
    ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    brand = db.relationship("BrandProfile", back_populates="briefs")
    skills = db.relationship("Skill", secondary=brief_skills)
    tools = db.relationship("AITool", secondary=brief_tools)
    applications = db.relationship("Application", back_populates="brief", cascade="all, delete-orphan")
    projects = db.relationship("Project", back_populates="brief")


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    brief_id = db.Column(db.Integer, db.ForeignKey("briefs.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("creator_profiles.id"), nullable=False)
    cover_message = db.Column(db.Text, default="")
    proposed_budget = db.Column(db.Integer, default=0)
    estimated_delivery = db.Column(db.String(80), default="")
    status = db.Column(db.String(40), default="Applied")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    brief = db.relationship("Brief", back_populates="applications")
    creator = db.relationship("CreatorProfile")
    portfolio_items = db.relationship("PortfolioProject", secondary=application_portfolio)


class Connection(db.Model):
    __tablename__ = "connections"
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | accepted | rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requester = db.relationship("User", foreign_keys=[requester_id])
    addressee = db.relationship("User", foreign_keys=[addressee_id])


class Follow(db.Model):
    __tablename__ = "follows"
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship("User", foreign_keys=[follower_id])
    followed = db.relationship("User", foreign_keys=[followed_id])


class SavedCreator(db.Model):
    __tablename__ = "saved_creators"
    id = db.Column(db.Integer, primary_key=True)
    brand_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("creator_profiles.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("CreatorProfile")
    brand_user = db.relationship("User")


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    attachment_type = db.Column(db.String(40), default="")  # portfolio | brief
    attachment_id = db.Column(db.Integer, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    brief_id = db.Column(db.Integer, db.ForeignKey("briefs.id"), nullable=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brand_profiles.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("creator_profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    stage = db.Column(db.String(40), default="Hire")
    budget = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    brief = db.relationship("Brief", back_populates="projects")
    brand = db.relationship("BrandProfile")
    creator = db.relationship("CreatorProfile")


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.String(255), default="")
    link = db.Column(db.String(200), default="")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("creator_profiles.id"), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey("brand_profiles.id"), nullable=False)
    rating = db.Column(db.Integer, default=5)
    body = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("CreatorProfile", back_populates="reviews")
    brand = db.relationship("BrandProfile")
