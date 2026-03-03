from django import forms
from .models import Ticket
from django.contrib.auth.forms import AuthenticationForm

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["tipo_falla", "prioridad", "descripcion"]

        widgets = {
            "tipo_falla": forms.Select(attrs={"class": "form-select"}),
            "prioridad": forms.Select(attrs={"class": "form-select"}),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),
        } 
class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'form-control'
        })