from django.db import models

# Create your models here.
class sso_result:
    def __init__(self, success, code, message, data):
        self.success = success
        self.code = code
        self.message = message
        self.data = data
