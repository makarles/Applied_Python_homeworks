from locust import HttpUser, task, between

class LinkShortenerUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_link(self):
        self.client.post("/links/shorten", json={
            "original_url": "https://example.com/some-long-url"
        })

    @task
    def get_link(self):
        # Здесь подставьте реально существующий short_code или настройте создание ссылки через setup
        self.client.get("/somecode")
