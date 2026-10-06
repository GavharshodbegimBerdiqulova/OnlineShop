import django.core.validators
from django.db import migrations, models


def empty_phone_to_null(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(phone='').update(phone=None)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z][A-Za-z0-9_]{2,19}$', "Username harf bilan boshlanishi, 3-20 belgi bo'lishi va faqat harf, raqam va _ dan iborat bo'lishi kerak")], verbose_name='Username'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, validators=[django.core.validators.RegexValidator('^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*\\.[A-Za-z]{2,}$', "Email noto'g'ri formatda")], verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=13, null=True, verbose_name='Telefon'),
        ),
        migrations.RunPython(empty_phone_to_null, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=13, null=True, unique=True, validators=[django.core.validators.RegexValidator('^\\+998\\d{9}$', "Telefon +998901234567 formatida bo'lishi kerak")], verbose_name='Telefon'),
        ),
    ]
