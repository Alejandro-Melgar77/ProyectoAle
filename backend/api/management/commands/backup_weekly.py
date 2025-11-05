from django.core.management.base import BaseCommand
import os
import subprocess
from datetime import datetime
from django.conf import settings

class Command(BaseCommand):
    help = 'Realiza un backup semanal de la base de datos'

    def handle(self, *args, **options):
        try:
            # Crear directorio de backups si no existe
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Generar nombre del archivo con fecha
            fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
            archivo_backup = os.path.join(backup_dir, f'backup_semanal_{fecha_actual}.sql')

            # Configuración de la base de datos desde settings
            db_settings = settings.DATABASES['default']
            
            # Comando para realizar el backup
            comando = [
                'pg_dump',
                f'--dbname=postgresql://{db_settings["USER"]}:{db_settings["PASSWORD"]}@{db_settings["HOST"]}:{db_settings["PORT"]}/{db_settings["NAME"]}',
                '-f', archivo_backup
            ]

            # Ejecutar el comando de backup
            subprocess.run(comando, check=True)
            
            self.stdout.write(
                self.style.SUCCESS(f'Backup creado exitosamente en: {archivo_backup}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear el backup: {str(e)}')
            )
