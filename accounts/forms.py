from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(label="Prénom", max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre Prénom'}))
    last_name = forms.CharField(label="Nom", max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre Nom'}))
    username = forms.CharField(label="Nom d'utilisateur", max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Identifiant'}))
    email = forms.EmailField(label="Adresse Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemple@email.com'}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name', '').strip().lower()
        last_name = cleaned_data.get('last_name', '').strip().lower()

        # Vérification qu'aucune personne n'a déjà ce duo Prénom + Nom
        if User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists():
            raise forms.ValidationError("Un compte existe déjà avec ce Prénom et ce Nom.")
        return cleaned_data