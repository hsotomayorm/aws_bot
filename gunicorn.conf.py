import os
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("WEB_THREADS", "1"))
timeout = int(os.getenv("WEB_TIMEOUT", "120"))
preload_app = True
accesslog = "-"
errorlog = "-"
