import django.db.models.deletion
import django.utils.timezone
import users.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Telefon')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='Rasm')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name="Tug'ilgan sana")),
                ('role', models.CharField(choices=[('customer', 'Mijoz'), ('admin', 'Admin')], default='customer', max_length=10)),
                ('is_verified', models.BooleanField(default=False, verbose_name='Email tasdiqlangan')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Foydalanuvchi',
                'verbose_name_plural': 'Foydalanuvchilar',
            },
            managers=[
                ('objects', users.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Masalan: Uy, Ish', max_length=50, verbose_name='Nomi')),
                ('city', models.CharField(max_length=100, verbose_name='Shahar')),
                ('street', models.CharField(max_length=255, verbose_name="Ko'cha")),
                ('zip_code', models.CharField(blank=True, max_length=10, verbose_name='Indeks')),
                ('is_default', models.BooleanField(default=False, verbose_name='Asosiy manzil')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Manzil',
                'verbose_name_plural': 'Manzillar',
            },
        ),
        migrations.CreateModel(
            name='VerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('purpose', models.CharField(choices=[('email', 'Email tasdiqlash'), ('reset', 'Parolni tiklash')], max_length=10)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tasdiqlash kodi',
                'verbose_name_plural': 'Tasdiqlash kodlari',
            },
        ),
    ]
