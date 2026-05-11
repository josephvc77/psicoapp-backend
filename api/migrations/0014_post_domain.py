from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_userprofile_bio_userprofile_goals'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='domain',
            field=models.CharField(choices=[('psychology', 'Psicología'), ('nutrition', 'Nutrición'), ('exercise', 'Ejercicio'), ('general', 'General')], default='general', max_length=20),
        ),
    ]
