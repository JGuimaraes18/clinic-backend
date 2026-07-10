from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clinic',
            name='banner',
            field=models.FileField(blank=True, null=True, upload_to='clinic_media/banners/'),
        ),
        migrations.AddField(
            model_name='clinic',
            name='logo',
            field=models.FileField(blank=True, null=True, upload_to='clinic_media/logos/'),
        ),
        migrations.AddField(
            model_name='clinic',
            name='primary_color',
            field=models.CharField(default='#0651ED', max_length=20),
        ),
        migrations.AddField(
            model_name='clinic',
            name='secondary_color',
            field=models.CharField(default='#4F46E5', max_length=20),
        ),
        migrations.AddField(
            model_name='clinic',
            name='theme',
            field=models.CharField(default='SYSTEM', max_length=20),
        ),
    ]
