# Generated by Django 5.1.6 on 2025-05-14 10:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth_section', '0001_initial'),
        ('leads_section', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('followup_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth_section.sales_manager_reg')),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leads_section.leads')),
            ],
            options={
                'unique_together': {('follower', 'lead', 'followup_date')},
            },
        ),
        migrations.CreateModel(
            name='Followup_status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=100)),
                ('note', models.CharField(max_length=200)),
                ('followup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='followup_section.followup')),
            ],
        ),
    ]
