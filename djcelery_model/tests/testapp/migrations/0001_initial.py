# Generated by Django 2.2.7 on 2019-11-10 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='JPEGFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('etag', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
