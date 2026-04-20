# api/forms.py (o la carpeta donde tengas tus vistas)
from django import forms
from django.contrib.auth.models import User

class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        # Le añadimos las clases de Tailwind directamente desde Python
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full bg-black text-white rounded border border-gray-700 p-2 focus:border-[#10b981] focus:ring-1 focus:ring-[#10b981] outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full bg-black text-white rounded border border-gray-700 p-2 focus:border-[#10b981] focus:ring-1 focus:ring-[#10b981] outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full bg-black text-white rounded border border-gray-700 p-2 focus:border-[#10b981] focus:ring-1 focus:ring-[#10b981] outline-none'}),
        }