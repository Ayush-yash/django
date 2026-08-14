from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=100)
    rollno = models.CharField(max_length=50)
    course = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
