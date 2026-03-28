#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:5003"

def get_token():
    """Get JWT token by logging in"""
    response = requests.post(timeout=10)
        f"{BASE_URL}/login",
        json={"username": "admin", "password": "afe2026"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get('token')
    return None

def test_endpoint(method, url, data=None, token=None, expected_status=None):
    """Test an API endpoint"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method == "GET":
        response = requests.get(timeout=10)url, headers=headers)
    elif method == "POST":
        response = requests.post(timeout=10)url, json=data, headers=headers)
    elif method == "PUT":
        response = requests.put(url, json=data, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    
    print(f"{method} {url}")
    print(f"  Status: {response.status_code} (expected: {expected_status})")
    if response.status_code != expected_status:
        print(f"  Response: {response.text[:200]}...")
    print()
    
    return response

def main():
    print("Testing all REST API endpoints with JWT authentication")
    print("=" * 60)
    
    # Get token
    token = get_token()
    if not token:
        print("Failed to get token")
        return
    
    print(f"Got token: {token[:50]}...\n")
    
    # Test endpoints without token (should fail)
    print("1. Testing without authentication (should return 401):")
    test_endpoint("GET", f"{BASE_URL}/api/articles", expected_status=401)
    test_endpoint("POST", f"{BASE_URL}/api/articles", data={"title": "Test"}, expected_status=401)
    
    # Test endpoints with token (should succeed)
    print("\n2. Testing with authentication (should succeed):")
    
    # Articles
    print("Articles endpoints:")
    test_endpoint("GET", f"{BASE_URL}/api/articles", token=token, expected_status=200)
    
    # Create an article for testing PUT and DELETE
    response = test_endpoint("POST", f"{BASE_URL}/api/articles", 
                           data={"title": "Test Article", "content": "Test content"}, 
                           token=token, expected_status=201)
    if response.status_code == 201:
        article_id = response.json().get('id')
        print(f"Created article with ID: {article_id}\n")
        
        # Test GET single article
        test_endpoint("GET", f"{BASE_URL}/api/articles/{article_id}", token=token, expected_status=200)
        
        # Test PUT (update) article
        test_endpoint("PUT", f"{BASE_URL}/api/articles/{article_id}", 
                     data={"title": "Updated Title", "content": "Updated content"}, 
                     token=token, expected_status=200)
        
        # Test DELETE article
        test_endpoint("DELETE", f"{BASE_URL}/api/articles/{article_id}", token=token, expected_status=200)
    
    # Categories
    print("\nCategories endpoints:")
    test_endpoint("GET", f"{BASE_URL}/api/categories", token=token, expected_status=200)
    
    # Create a category
    response = test_endpoint("POST", f"{BASE_URL}/api/categories", 
                           data={"name": "Test Category", "description": "Test"}, 
                           token=token, expected_status=201)
    if response.status_code == 201:
        category_id = response.json().get('id')
        print(f"Created category with ID: {category_id}\n")
        
        # Test GET single category
        test_endpoint("GET", f"{BASE_URL}/api/categories/{category_id}", token=token, expected_status=200)
        
        # Test PUT category
        test_endpoint("PUT", f"{BASE_URL}/api/categories/{category_id}", 
                     data={"name": "Updated Category"}, 
                     token=token, expected_status=200)
        
        # Test DELETE category
        test_endpoint("DELETE", f"{BASE_URL}/api/categories/{category_id}", token=token, expected_status=200)
    
    # Tags
    print("\nTags endpoints:")
    test_endpoint("GET", f"{BASE_URL}/api/tags", token=token, expected_status=200)
    
    # Create a tag
    response = test_endpoint("POST", f"{BASE_URL}/api/tags", 
                           data={"name": "Test Tag", "description": "Test"}, 
                           token=token, expected_status=201)
    if response.status_code == 201:
        tag_id = response.json().get('id')
        print(f"Created tag with ID: {tag_id}\n")
        
        # Test GET single tag
        test_endpoint("GET", f"{BASE_URL}/api/tags/{tag_id}", token=token, expected_status=200)
        
        # Test PUT tag
        test_endpoint("PUT", f"{BASE_URL}/api/tags/{tag_id}", 
                     data={"name": "Updated Tag"}, 
                     token=token, expected_status=200)
        
        # Test DELETE tag
        test_endpoint("DELETE", f"{BASE_URL}/api/tags/{tag_id}", token=token, expected_status=200)
    
    print("\n" + "=" * 60)
    print("All tests completed!")

if __name__ == "__main__":
    main()