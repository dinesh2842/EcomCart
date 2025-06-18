from django import forms
from .models import *

class ReviewForms(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject','review','rating']