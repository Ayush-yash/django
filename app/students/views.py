import os
from django.shortcuts import render, redirect
from .models import Student


def index(request):
    if request.method == "POST":
        Student.objects.create(
            name=request.POST["name"],
            rollno=request.POST["rollno"],
            course=request.POST["course"]
        )
        return redirect("/")

    students = Student.objects.all().order_by("-created")

    return render(request, "index.html", {
        "students": students,
        "pod_name": os.getenv("POD_NAME", "Unknown"),
        "node_name": os.getenv("NODE_NAME", "Unknown"),
    })
