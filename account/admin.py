from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.admin import UserAdmin

from .models import User, Child, Invintation
# Register your models here.



class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('__all__')

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_pasword(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = (
        (None, { 'fields' : (
            'username',
            'password',
        )}),
        ("Confirmation", { 'fields' : (
            'phone_code',
            'phone_confirmed',
        )}),
        ("Personal Info", { 'fields' : (
            'email',
            'first_name',
            'last_name',
            'phone',
            'children',
        )}),
        ("Permissions", { 'fields' : (
            'is_active',
            'is_staff',
            'is_superuser',
        )}),
        ("important Dates", { 'fields' : (
            'date_joined',
            'last_login',
        )}),
        ("Additional Fields", {'fields': (
            'visits',
            'my_invintations',
            'used_invintation',
        )}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Child)
admin.site.register(Invintation)