# api_test.py
import requests
import json

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.token = None
        self.headers = {"Content-Type": "application/json"}
    
    def set_auth_token(self, token):
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
    
    def test_user_registration(self):
        print("=== Testing User Registration ===")
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_user_login(self):
        print("=== Testing User Login ===")
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200:
            self.set_auth_token(result["access_token"])
        print()
        
        return response.status_code == 200
    
    def test_get_profile(self):
        print("=== Testing Get User Profile ===")
        response = requests.get(f"{BASE_URL}/profile", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_update_profile(self):
        print("=== Testing Update User Profile ===")
        update_data = {
            "email": "test@example.com",
            "password": "newpassword123",
            "full_name": "Updated Test User"
        }
        
        response = requests.put(f"{BASE_URL}/profile", json=update_data, headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_create_firm(self):
        print("=== Testing Create Firm ===")
        firm_data = {
            "name": "Test Company Inc.",
            "description": "A test company for demonstration",
            "address": "123 Test Street, Test City",
            "phone": "+1-555-123-4567",
            "email": "info@testcompany.com"
        }
        
        response = requests.post(f"{BASE_URL}/firms", json=firm_data, headers=self.headers)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        print()
        
        if response.status_code == 200:
            return result["id"]
        return None
    
    def test_get_firms(self):
        print("=== Testing Get User Firms ===")
        response = requests.get(f"{BASE_URL}/firms", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_get_firm_by_id(self, firm_id):
        print(f"=== Testing Get Firm by ID ({firm_id}) ===")
        response = requests.get(f"{BASE_URL}/firms/{firm_id}", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_update_firm(self, firm_id):
        print(f"=== Testing Update Firm ({firm_id}) ===")
        update_data = {
            "name": "Updated Test Company Inc.",
            "description": "An updated test company description"
        }
        
        response = requests.put(f"{BASE_URL}/firms/{firm_id}", json=update_data, headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_join_firm(self, firm_id):
        print(f"=== Testing Join Firm ({firm_id}) ===")
        response = requests.post(f"{BASE_URL}/firms/{firm_id}/join", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_logout(self):
        print("=== Testing User Logout ===")
        response = requests.post(f"{BASE_URL}/logout", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_delete_firm(self, firm_id):
        print(f"=== Testing Delete Firm ({firm_id}) ===")
        response = requests.delete(f"{BASE_URL}/firms/{firm_id}", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200
    
    def test_delete_user(self):
        print("=== Testing Delete User Account ===")
        response = requests.delete(f"{BASE_URL}/profile", headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        return response.status_code == 200

def main():
    tester = APITester()
    
    print("Starting API Tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("=" * 50)
    
    # Test user registration and authentication
    if not tester.test_user_registration():
        print("User registration failed. Trying to login with existing user...")
    
    if not tester.test_user_login():
        print("Login failed. Cannot continue with authenticated tests.")
        return
    
    # Test profile operations
    tester.test_get_profile()
    tester.test_update_profile()
    
    # Test firm operations
    firm_id = tester.test_create_firm()
    tester.test_get_firms()
    
    if firm_id:
        tester.test_get_firm_by_id(firm_id)
        tester.test_update_firm(firm_id)
        
        # Create a second user to test joining firm
        print("=== Creating Second User for Join Test ===")
        user2_data = {
            "email": "test2@example.com",
            "password": "testpassword123",
            "full_name": "Test User 2"
        }
        requests.post(f"{BASE_URL}/register", json=user2_data)
        
        # Login as second user
        login_data = {
            "email": "test2@example.com",
            "password": "testpassword123"
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            tester.set_auth_token(response.json()["access_token"])
            tester.test_join_firm(firm_id)
        
        # Switch back to first user
        login_data = {
            "email": "test@example.com",
            "password": "newpassword123"  # Updated password
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            tester.set_auth_token(response.json()["access_token"])
        
        # Test firm deletion
        tester.test_delete_firm(firm_id)
    
    # Test logout
    tester.test_logout()
    
    print("API Tests Completed!")

if __name__ == "__main__":
    main()