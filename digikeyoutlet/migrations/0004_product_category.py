# Generated by Django 5.1.4 on 2024-12-17 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digikeyoutlet', '0003_remove_product_digital_file_product_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.CharField(choices=[('adguard', 'AdGuard Products'), ('adobe', 'Adobe Products'), ('aida64', 'AIDA64 Products'), ('aiseesoft', 'Aiseesoft Products'), ('aomei', 'AOMEI Products'), ('ashampoo', 'Ashampoo Products'), ('autodesk', 'Autodesk Products'), ('bitdefender', 'Bitdefender Products'), ('ccleaner', 'CCleaner Products'), ('corel', 'Corel Products'), ('drivermagician', 'DriverMagician Products'), ('easeus', 'EaseUS Products'), ('eset', 'ESET Products'), ('glarysoft', 'Glarysoft Products'), ('kaspersky', 'Kaspersky Products'), ('macos', 'MacOs Software'), ('office2013', 'Microsoft Office 2013 Products'), ('office2016', 'Microsoft Office 2016 Products'), ('office2019', 'Microsoft Office 2019 Products'), ('office2021', 'Microsoft Office 2021 Products'), ('office2024', 'Microsoft Office 2024 Products'), ('office365', 'Microsoft Office 365 Products'), ('server', 'Microsoft Server Products'), ('sql', 'Microsoft SQL Server Products'), ('visualstudio', 'Microsoft Visual Studio Products'), ('windows10', 'Microsoft Windows 10 Products'), ('windows11', 'Microsoft Windows 11 Products'), ('windows7', 'Microsoft Windows 7 Products'), ('windows8', 'Microsoft Windows 8 Products'), ('mindmanager', 'MindManager Products'), ('nitro', 'Nitro Products'), ('spotify', 'Spotify Subscription'), ('subscription', 'Subscription and Credits'), ('symantec', 'Symantec Products'), ('vmware', 'VMware Products'), ('vpn', 'VPN Products')], default='adguard', max_length=50),
        ),
    ]