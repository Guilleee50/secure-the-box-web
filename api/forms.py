# api/forms.py (o la carpeta donde tengas tus vistas)
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm # Para el registro
from captcha.fields import CaptchaField # Importación del CAPTCHA
from captcha.fields import CaptchaField, CaptchaTextInput

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

class RegistroConCaptchaForm(UserCreationForm):
    captcha = CaptchaField(
        label="Verifica que eres humano",
        widget=CaptchaTextInput(attrs={
            'class': 'w-full bg-[#121212] text-white rounded border border-gray-700 p-3 mt-2 focus:border-[#10b981] outline-none',
            'placeholder': 'Escribe el código de la imagen'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Añadimos el email al formulario de registro por defecto
        fields = UserCreationForm.Meta.fields + ('email',)