import django.core.management.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='secret_key',
            field=models.CharField(default=django.core.management.utils.get_random_secret_key, max_length=255),
        ),
    ]