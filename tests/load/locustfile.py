"""
Phase 5: Load Testing Suite for Tally Sync Agent

Load test scenarios:
- Ramp up: 100 → 1000 concurrent users
- Sustained load: 500 users for 10 minutes
- Spike test: 100 → 2000 users
- Mixed workload (30% register, 20% login, 30% device, 20% data)
"""

from locust import HttpUser, task, between, events
from datetime import datetime
import json
import random

# ============================================================================
# Configuration
# ============================================================================

class LoadTestUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize user session"""
        self.user_id = f"user_{random.randint(1000, 9999)}"
        self.client_id = None
        self.access_token = None
        self.device_id = None

    # ========================================================================
    # Authentication Tasks (20% of traffic)
    # ========================================================================

    @task(10)
    def register_user(self):
        """Register new user"""
        payload = {
            "company_name": f"Company {self.user_id}",
            "email": f"{self.user_id}@test.com",
            "phone": "9999999999",
            "password": "SecurePassword123!"
        }

        with self.client.post(
            "/v1/auth/register",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.client_id = data.get("client_id")
                self.verification_token = data.get("verification_token")
                response.success()
            else:
                response.failure(f"Register failed: {response.status_code}")

    @task(10)
    def login_user(self):
        """Login user"""
        payload = {
            "email": f"{self.user_id}@test.com",
            "password": "SecurePassword123!"
        }

        with self.client.post(
            "/v1/auth/login",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.client_id = data.get("client_id")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # ========================================================================
    # Device Management Tasks (30% of traffic)
    # ========================================================================

    @task(15)
    def register_device(self):
        """Register new device"""
        if not self.access_token:
            return

        payload = {
            "device_name": f"PC-{self.user_id}",
            "os_version": "Windows 11",
            "agent_version": "1.0.0",
            "installation_key": f"TSA-TESTKEY-{random.randint(100000, 999999)}"
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        with self.client.post(
            "/v1/devices/register",
            json=payload,
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.device_id = data.get("device_id")
                response.success()
            else:
                response.failure(f"Device register failed: {response.status_code}")

    @task(15)
    def list_devices(self):
        """List registered devices"""
        if not self.access_token:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        with self.client.get(
            "/v1/devices/list",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List devices failed: {response.status_code}")

    # ========================================================================
    # Data Access Tasks (30% of traffic)
    # ========================================================================

    @task(15)
    def access_me_endpoint(self):
        """Access current user info"""
        if not self.access_token:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        with self.client.get(
            "/v1/auth/me",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Me endpoint failed: {response.status_code}")

    @task(15)
    def check_device_status(self):
        """Check device status"""
        if not self.access_token or not self.device_id:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}

        with self.client.get(
            f"/v1/devices/status/{self.device_id}",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Device status failed: {response.status_code}")

    # ========================================================================
    # Health Check Tasks (20% of traffic)
    # ========================================================================

    @task(10)
    def health_check(self):
        """Check application health"""
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# ============================================================================
# Test Event Listeners
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("\n" + "="*80)
    print("LOAD TEST STARTED")
    print("="*80)
    print(f"Start time: {datetime.now()}")
    print(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\n" + "="*80)
    print("LOAD TEST COMPLETED")
    print("="*80)
    print(f"Stop time: {datetime.now()}")
    print(f"User count: {environment.runner.user_count}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Called for each request"""
    if exception:
        print(f"❌ {request_type} {name}: {exception}")


# ============================================================================
# Test Scenarios
# ============================================================================

class RampUpScenario(LoadTestUser):
    """Ramp up: Gradually increase users from 100 to 1000"""
    # Duration: 30 minutes
    # 100 users → 5 min
    # 500 users → 10 min
    # 1000 users → 15 min
    # Hold at 1000 → 10 min


class SustainedLoadScenario(LoadTestUser):
    """Sustained load: Keep 500 users for 10 minutes"""
    # Duration: 10 minutes
    # Constant 500 users


class SpikeTestScenario(LoadTestUser):
    """Spike test: Sudden traffic increase from 100 to 2000 users"""
    # Duration: 15 minutes
    # 100 users → 1 min
    # Spike to 2000 users → 1 min
    # Hold at 2000 → 5 min
    # Reduce to 100 → 1 min
    # Steady → 7 min


# ============================================================================
# Test Configuration
# ============================================================================

if __name__ == "__main__":
    # To run tests:
    # locust -f tests/load/locustfile.py --host=http://localhost:8000
    # Then open http://localhost:8089 in browser
    pass
