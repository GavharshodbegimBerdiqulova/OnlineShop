from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_username_phone_validators'),
    ]

    operations = [
        migrations.DeleteModel(name='VerificationCode'),
        migrations.CreateModel(
            name='VerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact', models.CharField(db_index=True, max_length=255, verbose_name='Email yoki telefon')),
                ('code', models.CharField(max_length=4)),
                ('purpose', models.CharField(choices=[('signup', "Ro'yxatdan o'tish"), ('reset', 'Parolni tiklash')], max_length=10)),
                ('is_used', models.BooleanField(default=False)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Tasdiqlash kodi',
                'verbose_name_plural': 'Tasdiqlash kodlari',
            },
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*\\.[A-Za-z]{2,}$', "Email noto'g'ri formatda")], verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False, verbose_name='Kontakt tasdiqlangan'),
        ),
    ]
