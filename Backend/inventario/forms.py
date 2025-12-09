from django import forms
from django.contrib.auth.models import User
from .models import Cliente, Producto, Categoria, Proveedor

class RegistroClienteForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    password = forms.CharField(
        required=True,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña (mínimo 8 caracteres)'
        })
    )
    password_confirm = forms.CharField(
        required=True,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
    )
    
    class Meta:
        model = Cliente
        fields = ['fecha_nacimiento']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def save(self, commit=True):
        # Crear el usuario primero
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        
        # Crear el cliente vinculado al usuario
        cliente = super().save(commit=False)
        cliente.user = user
        
        if commit:
            cliente.save()
        
        return cliente


class ProductoForm(forms.ModelForm):
    """Formulario para crear y editar productos en el admin"""
    
    class Meta:
        model = Producto
        fields = ['nombre', 'sku', 'descripcion', 'precio', 'costo', 'stock', 'stock_minimo', 'categoria', 'proveedor', 'imagen_url', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto',
                'required': True
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU único del producto',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto',
                'rows': 4
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Precio del producto',
                'step': '0.01',
                'required': True
            }),
            'costo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Costo del producto',
                'step': '0.01'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cantidad en stock',
                'required': True
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stock mínimo',
                'value': 5
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'proveedor': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'imagen_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL de imagen (Imgur, Cloudinary, etc.)'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre or len(nombre.strip()) == 0:
            raise forms.ValidationError('El nombre del producto es obligatorio.')
        return nombre
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock
