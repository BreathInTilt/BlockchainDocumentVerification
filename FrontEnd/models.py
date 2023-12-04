from django.db import models


class Document(models.Model):
    upload = models.FileField(upload_to='documents/')
    file_hash = models.CharField(max_length=64, blank=True)  # Поле для хранения хеша файла
    created_at = models.DateTimeField(auto_now_add=True)  # Дата и время создания
