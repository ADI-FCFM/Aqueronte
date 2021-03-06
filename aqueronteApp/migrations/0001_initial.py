# Generated by Django 2.1.4 on 2019-01-18 14:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tickets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_cas', models.CharField(max_length=256)),
                ('fecha', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Tokens',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=256)),
                ('refresh_token', models.CharField(max_length=256)),
                ('fecha_exp', models.DateTimeField()),
                ('estado', models.BooleanField()),
                ('fecha_c', models.DateTimeField()),
                ('fecha_m', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Usuarios',
            fields=[
                ('pers_id', models.CharField(max_length=60, primary_key=True, serialize=False)),
                ('nombres', models.CharField(max_length=60)),
                ('apellidos', models.CharField(max_length=60)),
                ('fecha_c', models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name='tokens',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aqueronteApp.Usuarios'),
        ),
        migrations.AddField(
            model_name='tickets',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aqueronteApp.Usuarios'),
        ),
    ]
