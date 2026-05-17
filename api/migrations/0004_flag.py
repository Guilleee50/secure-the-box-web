from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_socprofile_normativa_aceptada'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=200, unique=True)),
                ('creada_en', models.DateTimeField()),
                ('usada', models.BooleanField(default=False)),
                ('usada_en', models.DateTimeField(blank=True, null=True)),
                ('maquina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.maquina')),
                ('usada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Flag',
                'verbose_name_plural': 'Flags',
            },
        ),
    ]
