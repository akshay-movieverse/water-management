from django import forms
from .models import Unit, Subunit, CustomUser

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'city']

class SubunitForm(forms.ModelForm):
    class Meta:
        model = Subunit
        fields = ['name']

class ManagerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'unit', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_manager = True
        if commit:
            user.save()
        return user
