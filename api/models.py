from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    machine_name = models.CharField(max_length=100)
    points = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.machine_name}: {self.points}"
