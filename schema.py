#!/usr/bin/env python3
"""
GraphQL Schema for KB Portal
"""
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import bleach

# Allowed HTML tags for article content
ALLOWED_TAGS = ['p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'blockquote']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title', 'class'], 'code': ['class'], 'pre': ['class']}

def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    if not text:
        return text
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

# PostgreSQL connection settings
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = '5432'
POSTGRES_DB = 'kb_portal'
POSTGRES_USER = 'kenchan'
POSTGRES_PASSWORD = 'ken123456'

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
# Use psycopg for PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define SQLAlchemy models
class Category(db.Model):
    __tablename__ = 'kb_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    parent_id = db.Column(db.Integer, db.ForeignKey('kb_categories.id'))
    created_at = db.Column(db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

class Article(db.Model):
    __tablename__ = 'kb_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('kb_categories.id'))
    author = db.Column(db.String)
    status = db.Column(db.String, default='draft')  # draft, published, archived
    view_count = db.Column(db.Integer, default=0)
    tags = db.Column(db.String)  # Comma-separated tags
    created_at = db.Column(db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

class ArticleRevision(db.Model):
    __tablename__ = 'kb_article_revisions'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('kb_articles.id'))
    title = db.Column(db.String)
    content = db.Column(db.Text)
    author = db.Column(db.String)
    revision_note = db.Column(db.String)
    created_at = db.Column(db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

class Tag(db.Model):
    __tablename__ = 'kb_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String)
    created_at = db.Column(db.String, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# Define GraphQL Object Types
class CategoryObject(SQLAlchemyObjectType):
    class Meta:
        model = Category
        interfaces = (graphene.relay.Node,)

class ArticleObject(SQLAlchemyObjectType):
    class Meta:
        model = Article
        interfaces = (graphene.relay.Node,)

class ArticleRevisionObject(SQLAlchemyObjectType):
    class Meta:
        model = ArticleRevision
        interfaces = (graphene.relay.Node,)

class TagObject(SQLAlchemyObjectType):
    class Meta:
        model = Tag
        interfaces = (graphene.relay.Node,)

# Authentication decorator for GraphQL
def require_login(func):
    """Decorator to require login for GraphQL resolvers"""
    from functools import wraps
    from flask import session
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if user is logged in via session
        if not session.get('logged_in'):
            raise Exception('Authentication required')
        return func(*args, **kwargs)
    return wrapper

# Define Queries
class Query(graphene.ObjectType):
    all_articles = SQLAlchemyConnectionField(ArticleObject)
    article = graphene.Field(ArticleObject, id=graphene.Int())
    articles_by_category = SQLAlchemyConnectionField(ArticleObject, category_id=graphene.Int())
    articles_by_tag = SQLAlchemyConnectionField(ArticleObject, tag=graphene.String())
    search_articles = SQLAlchemyConnectionField(ArticleObject, query=graphene.String())
    
    all_categories = SQLAlchemyConnectionField(CategoryObject)
    category = graphene.Field(CategoryObject, id=graphene.Int())
    
    all_tags = SQLAlchemyConnectionField(TagObject)
    tag = graphene.Field(TagObject, id=graphene.Int())
    tag_by_name = graphene.Field(TagObject, name=graphene.String())
    
    all_revisions = SQLAlchemyConnectionField(ArticleRevisionObject)
    revisions_by_article = SQLAlchemyConnectionField(ArticleRevisionObject, article_id=graphene.Int())

    @require_login
    def resolve_all_articles(self, info, **kwargs):
        return Article.query
    
    @require_login
    def resolve_article(self, info, id):
        return Article.query.get(id)
    
    @require_login
    def resolve_articles_by_category(self, info, category_id):
        return Article.query.filter_by(category_id=category_id).all()
    
    @require_login
    def resolve_articles_by_tag(self, info, tag):
        return Article.query.filter(Article.tags.contains(tag)).all()
    
    @require_login
    def resolve_search_articles(self, info, query):
        search = f"%{query}%"
        return Article.query.filter(
            (Article.title.ilike(search)) | 
            (Article.content.ilike(search))
        ).all()
    
    @require_login
    def resolve_all_categories(self, info, **kwargs):
        return Category.query
    
    @require_login
    def resolve_category(self, info, id):
        return Category.query.get(id)
    
    @require_login
    def resolve_all_tags(self, info, **kwargs):
        return Tag.query
    
    @require_login
    def resolve_tag(self, info, id):
        return Tag.query.get(id)
    
    @require_login
    def resolve_tag_by_name(self, info, name):
        return Tag.query.filter_by(name=name).first()
    
    @require_login
    def resolve_all_revisions(self, info, **kwargs):
        return ArticleRevision.query
    
    @require_login
    def resolve_revisions_by_article(self, info, article_id):
        return ArticleRevision.query.filter_by(article_id=article_id).order_by(ArticleRevision.created_at.desc()).all()

# Define Mutations
class CreateCategory(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        parent_id = graphene.Int()
    
    category = graphene.Field(CategoryObject)
    
    @staticmethod
    @require_login
    def mutate(root, info, name, description=None, parent_id=None):
        category = Category(name=name, description=description, parent_id=parent_id)
        db.session.add(category)
        db.session.commit()
        return CreateCategory(category=category)

class UpdateCategory(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String()
        description = graphene.String()
    
    category = graphene.Field(CategoryObject)
    
    @staticmethod
    @require_login
    def mutate(root, info, id, name=None, description=None):
        category = Category.query.get(id)
        if category:
            if name:
                category.name = name
            if description:
                category.description = description
            category.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.commit()
        return UpdateCategory(category=category)

class DeleteCategory(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    
    @staticmethod
    @require_login
    def mutate(root, info, id):
        category = Category.query.get(id)
        if category:
            db.session.delete(category)
            db.session.commit()
            return DeleteCategory(success=True)
        return DeleteCategory(success=False)

class CreateArticle(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String()
        category_id = graphene.Int()
        author = graphene.String()
        status = graphene.String()
        tags = graphene.String()
    
    article = graphene.Field(ArticleObject)
    
    @staticmethod
    @require_login
    def mutate(root, info, title, content=None, category_id=None, author=None, status='draft', tags=None):
        # Sanitize inputs to prevent XSS
        sanitized_title = sanitize_input(title)
        sanitized_content = sanitize_input(content) if content else None
        sanitized_tags = sanitize_input(tags) if tags else None
        
        article = Article(
            title=sanitized_title,
            content=sanitized_content,
            category_id=category_id,
            author=author,
            status=status,
            tags=sanitized_tags
        )
        db.session.add(article)
        db.session.commit()
        
        # Create initial revision - use SANITIZED values to prevent XSS
        revision = ArticleRevision(
            article_id=article.id,
            title=sanitized_title,
            content=sanitized_content,
            author=author,
            revision_note='Initial creation'
        )
        db.session.add(revision)
        db.session.commit()
        
        return CreateArticle(article=article)

class UpdateArticle(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String()
        content = graphene.String()
        category_id = graphene.Int()
        status = graphene.String()
        tags = graphene.String()
        revision_note = graphene.String()
    
    article = graphene.Field(ArticleObject)
    
    @staticmethod
    @require_login
    def mutate(root, info, id, title=None, content=None, category_id=None, status=None, tags=None, revision_note=None):
        article = Article.query.get(id)
        if article:
            # Get user from Flask session instead of info.context.get()
            from flask import session
            author = session.get('user', 'anonymous')
            
            # Sanitize inputs to prevent XSS
            sanitized_title = sanitize_input(title) if title else None
            sanitized_content = sanitize_input(content) if content else None
            sanitized_tags = sanitize_input(tags) if tags else None
            
            # Create revision before updating - use SANITIZED values to prevent XSS
            revision = ArticleRevision(
                article_id=article.id,
                title=sanitize_input(article.title) if article.title else None,
                content=sanitize_input(article.content) if article.content else None,
                author=author,
                revision_note=revision_note or 'Updated'
            )
            db.session.add(revision)
            
            if sanitized_title:
                article.title = sanitized_title
            if sanitized_content is not None:
                article.content = sanitized_content
            if category_id is not None:
                article.category_id = category_id
            if status:
                article.status = status
            if sanitized_tags:
                article.tags = sanitized_tags
            article.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.commit()
            
        return UpdateArticle(article=article)

class DeleteArticle(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
    
    ok = graphene.Boolean()
    article = graphene.Field(ArticleObject)
    
    @staticmethod
    @require_login
    def mutate(root, info, id):
        article = Article.query.get(id)
        if article:
            # Delete related revisions first
            ArticleRevision.query.filter_by(article_id=id).delete()
            db.session.delete(article)
            db.session.commit()
            return DeleteArticle(ok=True, article=None)
        return DeleteArticle(ok=False, article=None)

class CreateTag(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
    
    tag = graphene.Field(TagObject)
    
    @staticmethod
    @require_login
    def mutate(root, info, name, description=None):
        tag = Tag(name=name, description=description)
        db.session.add(tag)
        db.session.commit()
        return CreateTag(tag=tag)

class DeleteTag(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    
    @staticmethod
    @require_login
    def mutate(root, info, id):
        tag = Tag.query.get(id)
        if tag:
            db.session.delete(tag)
            db.session.commit()
            return DeleteTag(success=True)
        return DeleteTag(success=False)

class Mutation(graphene.ObjectType):
    create_category = CreateCategory.Field()
    update_category = UpdateCategory.Field()
    delete_category = DeleteCategory.Field()
    
    create_article = CreateArticle.Field()
    update_article = UpdateArticle.Field()
    delete_article = DeleteArticle.Field()
    
    create_tag = CreateTag.Field()
    delete_tag = DeleteTag.Field()

# Create schema
schema = graphene.Schema(query=Query, mutation=Mutation)

# Create tables
with app.app_context():
    db.create_all()
    print("✅ KB Portal database tables created successfully!")
