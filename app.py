#!/usr/bin/env python3
# CI Test trigger - $(date)
"""
KB Portal Backend with GraphQL API
"""

import os
import sys

# Determine port: CLI arg --port X, env PORT, or default 5003
DEPLOY_PORT = 5003
if '--port' in sys.argv:
    idx = sys.argv.index('--port')
    DEPLOY_PORT = int(sys.argv[idx + 1])
elif os.environ.get('PORT'):
    DEPLOY_PORT = int(os.environ.get('PORT'))
elif os.environ.get('DEPLOY_PORT'):
    DEPLOY_PORT = int(os.environ.get('DEPLOY_PORT'))

from flask import Flask, render_template_string, request, redirect, url_for, g, session, jsonify, send_from_directory, make_response
from flask_cors import CORS
from flask_graphql import GraphQLView
import os
from datetime import datetime

# Import GraphQL schema
from schema import app as flask_app, db, schema

app = flask_app
CORS(app, supports_credentials=True, 
     origins=[
         # Dev environment
         'http://192.168.140.149:3003', 'http://localhost:3003', 'http://127.0.0.1:3003',
         # UAT environment
         'http://192.168.140.149:3004', 'http://localhost:3004', 'http://127.0.0.1:3004',
     ],
     expose_headers=['Set-Cookie'],
     allow_headers=['Content-Type', 'Authorization'])

app.secret_key = 'kb_portal_secret_key_2026'

VERSION = "v1.0.2"
BUILD_DATE = datetime.now().strftime('%Y-%m-%d %H:%M')

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "afe2026"

# Import JWT authentication
from jwt_auth import jwt_required, generate_token, verify_token

# Add GraphQL endpoint with authentication
class AuthGraphQLView(GraphQLView):
    def dispatch_request(self):
        # Skip auth check for introspection queries (needed for GraphiQL)
        if request.method == 'POST' and request.is_json:
            data = request.get_json()
            query = data.get('query', '')
            
            # Allow introspection queries without auth (for GraphiQL)
            is_introspection = 'IntrospectionQuery' in query or '__schema' in query
            
            if not is_introspection and not session.get('logged_in'):
                return jsonify({'errors': [{'message': 'Authentication required. Please login first.'}]})
        
        return super().dispatch_request()

app.add_url_rule('/graphql', view_func=AuthGraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True
))

# Login required decorator
def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - KB Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #1a2533 0%, #2c3e50 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 10px; font-size: 24px; }
        .subtitle { text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 14px; }
        .version { text-align: center; color: #95a5a6; font-size: 12px; margin-top: 20px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: #555; }
        input { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 15px;
        }
        input:focus { outline: none; border-color: #3498db; }
        .btn {
            width: 100%;
            padding: 12px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn:hover { background: #2980b9; }
        .error { color: #e74c3c; text-align: center; margin-bottom: 15px; font-size: 14px; }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo i { font-size: 48px; color: #3498db; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <i class="fas fa-book"></i>
        </div>
        <h1>KB Portal</h1>
        <p class="subtitle">Knowledge Base Management System</p>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST" action="/login">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        <p class="version">{{ version }} | {{ build_date }}</p>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>KB Portal - Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Roboto, sans-serif; 
            background: #f5f6fa;
        }
        .header {
            background: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { color: #2c3e50; font-size: 20px; }
        .header .user { color: #7f8c8d; font-size: 14px; }
        .header .logout { color: #e74c3c; text-decoration: none; }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .stat-card h3 { color: #7f8c8d; font-size: 14px; margin-bottom: 10px; }
        .stat-card .number { color: #2c3e50; font-size: 32px; font-weight: bold; }
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .card h2 { color: #2c3e50; margin-bottom: 20px; font-size: 18px; }
        .btn {
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover { background: #2980b9; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { color: #7f8c8d; font-weight: 500; }
        tr:hover { background: #f8f9fa; }
        .status { padding: 4px 10px; border-radius: 12px; font-size: 12px; }
        .status.published { background: #d4edda; color: #155724; }
        .status.draft { background: #fff3cd; color: #856404; }
        .status.archived { background: #e2e3e5; color: #383d41; }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-book"></i> KB Portal</h1>
        <div>
            <span class="user">Welcome, {{ username }}</span>
            <span style="margin: 0 10px;">|</span>
            <a href="/logout" class="logout">Logout</a>
        </div>
    </div>
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Articles</h3>
                <div class="number" id="totalArticles">-</div>
            </div>
            <div class="stat-card">
                <h3>Published</h3>
                <div class="number" id="publishedArticles">-</div>
            </div>
            <div class="stat-card">
                <h3>Categories</h3>
                <div class="number" id="totalCategories">-</div>
            </div>
            <div class="stat-card">
                <h3>Tags</h3>
                <div class="number" id="totalTags">-</div>
            </div>
        </div>
        <div class="card">
            <h2>Quick Actions</h2>
            <a href="/graphql" target="_blank" class="btn"><i class="fas fa-code"></i> GraphQL Playground</a>
            <a href="/api/articles" class="btn" style="margin-left: 10px;"><i class="fas fa-list"></i> View Articles API</a>
        </div>
        <div class="card">
            <h2>Recent Articles</h2>
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Author</th>
                        <th>Status</th>
                        <th>Updated</th>
                    </tr>
                </thead>
                <tbody id="recentArticles"></tbody>
            </table>
        </div>
    </div>
    <script>
        const GRAPHQL_ENDPOINT = '/graphql';
        
        async function fetchStats() {
            const query = `query {
                allArticles { totalCount }
                allCategories { totalCount }
                allTags { totalCount }
            }`;
            
            try {
                const response = await fetch(GRAPHQL_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });
                const data = await response.json();
                
                if (data.data) {
                    document.getElementById('totalArticles').textContent = data.data.allArticles.totalCount || 0;
                    document.getElementById('totalCategories').textContent = data.data.allCategories.totalCount || 0;
                    document.getElementById('totalTags').textContent = data.data.allTags.totalCount || 0;
                }
            } catch (e) {
                console.error('Error fetching stats:', e);
            }
            
            // Fetch published count
            const pubQuery = `query { articlesByStatus: allArticles( filters: { status: { eq: "published" } }) { totalCount } }`;
            try {
                const resp = await fetch(GRAPHQL_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: pubQuery })
                });
                const d = await resp.json();
                if (d.data && d.data.articlesByStatus) {
                    document.getElementById('publishedArticles').textContent = d.data.articlesByStatus.totalCount || 0;
                }
            } catch(e) {}
        }
        
        async function fetchRecentArticles() {
            const query = `query {
                allArticles(first: 5, orderBy: UPDATED_AT_DESC) {
                    edges {
                        node {
                            id
                            title
                            author
                            status
                            updatedAt
                            categoryId
                        }
                    }
                }
            }`;
            
            try {
                const response = await fetch(GRAPHQL_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });
                const data = await response.json();
                
                if (data.data && data.data.allArticles) {
                    const tbody = document.getElementById('recentArticles');
                    tbody.innerHTML = data.data.allArticles.edges.map(edge => `
                        <tr>
                            <td>${edge.node.title || 'Untitled'}</td>
                            <td>${edge.node.categoryId || '-'}</td>
                            <td>${edge.node.author || '-'}</td>
                            <td><span class="status ${edge.node.status}">${edge.node.status || 'draft'}</span></td>
                            <td>${edge.node.updatedAt ? new Date(edge.node.updatedAt).toLocaleDateString() : '-'}</td>
                        </tr>
                    `).join('');
                }
            } catch (e) {
                console.error('Error fetching articles:', e);
            }
        }
        
        fetchStats();
        fetchRecentArticles();
    </script>
</body>
</html>
'''

@app.route('/')
@require_login
def index():
    return render_template_string(DASHBOARD_TEMPLATE, version=VERSION, build_date=BUILD_DATE, username=session.get('username', 'Admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Check if request is JSON
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            # Form data
            username = request.form.get('username')
            password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Set session for traditional login (for GraphQL and web interface)
            session['logged_in'] = True
            session['username'] = username
            
            # Generate JWT token for REST API
            token = generate_token(username)
            
            # Return JSON response for API requests
            if request.is_json or request.args.get('api') == 'true':
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {'username': username}
                })
            
            # For web form login, set token in cookie and redirect
            response = make_response(redirect('/'))
            response.set_cookie('kb_token', token, httponly=True, samesite='Lax')
            return response
        else:
            error = 'Invalid username or password'
            
            # Return JSON error for API requests
            if request.is_json or request.args.get('api') == 'true':
                return jsonify({'success': False, 'error': error}), 401
    
    # For GET requests, render login page
    return render_template_string(LOGIN_TEMPLATE, version=VERSION, build_date=BUILD_DATE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# API endpoints for Next.js frontend
@app.route('/api/articles', methods=['GET', 'POST'])
@jwt_required
def api_articles():
    from schema import Article, Category, Tag
    
    if request.method == 'GET':
        articles = Article.query.order_by(Article.updated_at.desc()).all()
        return jsonify([{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'author': a.author,
            'status': a.status,
            'tags': a.tags,
            'viewCount': a.view_count,
            'categoryId': a.category_id,
            'createdAt': a.created_at,
            'updatedAt': a.updated_at
        } for a in articles])
    
    elif request.method == 'POST':
        # Create new article
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        article = Article(
            title=data['title'],
            content=data.get('content', ''),
            author=data.get('author', ''),
            status=data.get('status', 'draft'),
            tags=data.get('tags', ''),
            category_id=data.get('categoryId'),
            view_count=0
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'author': article.author,
            'status': article.status,
            'tags': article.tags,
            'viewCount': article.view_count,
            'categoryId': article.category_id,
            'createdAt': article.created_at,
            'updatedAt': article.updated_at
        }), 201

@app.route('/api/articles/<int:article_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def api_article(article_id):
    from schema import Article
    
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'error': 'Article not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'author': article.author,
            'status': article.status,
            'tags': article.tags,
            'viewCount': article.view_count,
            'categoryId': article.category_id,
            'createdAt': article.created_at,
            'updatedAt': article.updated_at
        })
    
    elif request.method == 'PUT':
        # Update article
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'title' in data:
            article.title = data['title']
        if 'content' in data:
            article.content = data['content']
        if 'author' in data:
            article.author = data['author']
        if 'status' in data:
            article.status = data['status']
        if 'tags' in data:
            article.tags = data['tags']
        if 'categoryId' in data:
            article.category_id = data['categoryId']
        
        db.session.commit()
        
        return jsonify({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'author': article.author,
            'status': article.status,
            'tags': article.tags,
            'viewCount': article.view_count,
            'categoryId': article.category_id,
            'createdAt': article.created_at,
            'updatedAt': article.updated_at
        })
    
    elif request.method == 'DELETE':
        db.session.delete(article)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Article deleted'})

@app.route('/api/categories', methods=['GET', 'POST'])
@jwt_required
def api_categories():
    from schema import Category
    
    if request.method == 'GET':
        categories = Category.query.all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'parentId': c.parent_id
        } for c in categories])
    
    elif request.method == 'POST':
        # Create new category
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            parent_id=data.get('parentId')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parentId': category.parent_id
        }), 201

@app.route('/api/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def api_category(category_id):
    from schema import Category
    
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parentId': category.parent_id
        })
    
    elif request.method == 'PUT':
        # Update category
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'parentId' in data:
            category.parent_id = data['parentId']
        
        db.session.commit()
        
        return jsonify({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parentId': category.parent_id
        })
    
    elif request.method == 'DELETE':
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Category deleted'})

@app.route('/api/tags', methods=['GET', 'POST'])
@jwt_required
def api_tags():
    from schema import Tag
    
    if request.method == 'GET':
        tags = Tag.query.all()
        return jsonify([{
            'id': t.id,
            'name': t.name,
            'description': t.description
        } for t in tags])
    
    elif request.method == 'POST':
        # Create new tag
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        tag = Tag(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'id': tag.id,
            'name': tag.name,
            'description': tag.description
        }), 201

@app.route('/api/tags/<int:tag_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def api_tag(tag_id):
    from schema import Tag
    
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': tag.id,
            'name': tag.name,
            'description': tag.description
        })
    
    elif request.method == 'PUT':
        # Update tag
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'name' in data:
            tag.name = data['name']
        if 'description' in data:
            tag.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'id': tag.id,
            'name': tag.name,
            'description': tag.description
        })
    
    elif request.method == 'DELETE':
        db.session.delete(tag)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tag deleted'})

@app.route('/api/stats', methods=['GET'])
@jwt_required
def api_stats():
    from schema import Article, Category, Tag
    
    total_articles = Article.query.count()
    published_articles = Article.query.filter_by(status='published').count()
    draft_articles = Article.query.filter_by(status='draft').count()
    archived_articles = Article.query.filter_by(status='archived').count()
    total_categories = Category.query.count()
    total_tags = Tag.query.count()
    total_views = db.session.query(db.func.sum(Article.view_count)).scalar() or 0
    
    return jsonify({
        'totalArticles': total_articles,
        'publishedArticles': published_articles,
        'draftArticles': draft_articles,
        'archivedArticles': archived_articles,
        'totalCategories': total_categories,
        'totalTags': total_tags,
        'totalViews': total_views
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': VERSION, 'port': DEPLOY_PORT})

if __name__ == '__main__':
    print(f"🚀 Starting KB Portal Backend on port {DEPLOY_PORT}...")
    print(f"📚 GraphQL endpoint: http://localhost:{DEPLOY_PORT}/graphql")
    print(f"🔐 Login: admin / afe2026")
    app.run(host='0.0.0.0', port=DEPLOY_PORT, debug=True)
