# persona/management/commands/create_test_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from persona.models import (
    Persona, PersonaEstudiante, PersonaDocente, PersonaNoDocente,
    Dependencia, Carrera, Area, Beca, PersonaBeca, PersonaIngresante,
    PersonaEgresado
)
from comedor.models import (
    TipoMenu, ConfiguracionMenu, BeneficioComedor, CertificadoCeliaco
)
from datetime import date, timedelta
from django.core.files.base import ContentFile
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea usuarios de prueba completos con diferentes roles para el sistema de comedor'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Elimina los usuarios de prueba existentes antes de crearlos',
        )

    def handle(self, *args, **kwargs):
        clean = kwargs.get('clean', False)

        if clean:
            self.stdout.write(self.style.WARNING('Eliminando usuarios de prueba existentes...'))

            # Lista de correos a eliminar
            correos_test = [
                'admin@comedor.uncu.edu.ar',
                'estudiante1@comedor.uncu.edu.ar', 'estudiante2@comedor.uncu.edu.ar',
                'estudiante3@comedor.uncu.edu.ar', 'ingresante1@comedor.uncu.edu.ar',
                'egresado1@comedor.uncu.edu.ar', 'docente1@comedor.uncu.edu.ar',
                'docente2@comedor.uncu.edu.ar', 'nodocente1@comedor.uncu.edu.ar',
                'nodocente2@comedor.uncu.edu.ar', 'admin.comedor@comedor.uncu.edu.ar'
            ]

            # Lista de documentos a eliminar
            documentos_test = [
                '12345678', '23456789', '34567890', '45678901', '56789012',
                '67890123', '78901234', '89012345', '90123456', '01234567',
                'TEMP_admin', '99999999'
            ]

            # Eliminar Personas primero (esto eliminará en cascada los datos relacionados)
            personas_eliminadas = Persona.objects.filter(
                models.Q(documento__in=documentos_test) |
                models.Q(correo__in=correos_test)
            ).count()
            Persona.objects.filter(
                models.Q(documento__in=documentos_test) |
                models.Q(correo__in=correos_test)
            ).delete()
            self.stdout.write(f'  • {personas_eliminadas} personas eliminadas')

            # Eliminar usuarios (incluyendo los creados por el signal)
            usernames_test = [
                'admin', 'estudiante1', 'estudiante2', 'estudiante3',
                'docente1', 'docente2', 'nodocente1', 'nodocente2',
                'admin_comedor', 'ingresante1', 'egresado1'
            ]
            usuarios_eliminados = User.objects.filter(
                models.Q(username__in=usernames_test) |
                models.Q(email__in=correos_test)
            ).count()
            User.objects.filter(
                models.Q(username__in=usernames_test) |
                models.Q(email__in=correos_test)
            ).delete()
            self.stdout.write(f'  • {usuarios_eliminados} usuarios eliminados')
            self.stdout.write(self.style.SUCCESS('  ✓ Limpieza completada'))

        self.stdout.write(self.style.SUCCESS('\nCreando estructura base...'))

        # ==================== DEPENDENCIAS Y CARRERAS ====================
        dependencias_data = [
            {'nombre': 'Facultad de Ingeniería', 'codigo': 'FI'},
            {'nombre': 'Facultad de Ciencias Exactas y Naturales', 'codigo': 'FCEN'},
            {'nombre': 'Facultad de Ciencias Médicas', 'codigo': 'FCM'},
            {'nombre': 'Facultad de Ciencias Económicas', 'codigo': 'FCE'},
        ]

        dependencias = {}
        for dep_data in dependencias_data:
            dep, _ = Dependencia.objects.get_or_create(
                nombre=dep_data['nombre'],
                defaults={'codigo': dep_data['codigo']}
            )
            dependencias[dep_data['codigo']] = dep
            self.stdout.write(f'  ✓ Dependencia: {dep.nombre}')

        # Carreras
        carreras_data = [
            {'codigo': 'ING001', 'nombre': 'Ingeniería en Sistemas', 'dep': 'FI', 'plan': 'Plan 2015', 'anio': 2015},
            {'codigo': 'ING002', 'nombre': 'Ingeniería Civil', 'dep': 'FI', 'plan': 'Plan 2018', 'anio': 2018},
            {'codigo': 'LIC001', 'nombre': 'Licenciatura en Ciencias Biológicas', 'dep': 'FCEN', 'plan': 'Plan 2020',
             'anio': 2020},
            {'codigo': 'MED001', 'nombre': 'Medicina', 'dep': 'FCM', 'plan': 'Plan 2019', 'anio': 2019},
            {'codigo': 'CONT001', 'nombre': 'Contador Público', 'dep': 'FCE', 'plan': 'Plan 2016', 'anio': 2016},
        ]

        carreras = {}
        for carr_data in carreras_data:
            carr, _ = Carrera.objects.get_or_create(
                codigo=carr_data['codigo'],
                defaults={
                    'nombre': carr_data['nombre'],
                    'dependencia': dependencias[carr_data['dep']],
                    'plan_estudio': carr_data['plan'],
                    'anio_programa': carr_data['anio']
                }
            )
            carreras[carr_data['codigo']] = carr
            self.stdout.write(f'  ✓ Carrera: {carr.nombre}')

        # Áreas
        areas_data = ['Administración', 'Sistemas', 'Biblioteca', 'Mantenimiento', 'Recursos Humanos']
        areas = {}
        for area_name in areas_data:
            area, _ = Area.objects.get_or_create(nombre=area_name)
            areas[area_name] = area
            self.stdout.write(f'  ✓ Área: {area.nombre}')

        # ==================== TIPOS DE MENÚ ====================
        self.stdout.write(self.style.SUCCESS('\nCreando tipos de menú...'))

        menu_comun, _ = TipoMenu.objects.get_or_create(
            tipo='comun',
            defaults={
                'nombre': 'Menú Común',
                'descripcion': 'Menú estándar del día',
                'precio': Decimal('1500.00'),
                'activo': True
            }
        )

        menu_vegetariano, _ = TipoMenu.objects.get_or_create(
            tipo='vegetariano',
            defaults={
                'nombre': 'Menú Vegetariano',
                'descripcion': 'Menú sin carnes',
                'precio': Decimal('1500.00'),
                'activo': True
            }
        )

        menu_celiaco_comun, _ = TipoMenu.objects.get_or_create(
            tipo='celiaco_comun',
            defaults={
                'nombre': 'Menú Celíaco Común',
                'descripcion': 'Menú común sin TACC',
                'precio': Decimal('1800.00'),
                'activo': True
            }
        )

        menu_celiaco_vegetariano, _ = TipoMenu.objects.get_or_create(
            tipo='celiaco_vegetariano',
            defaults={
                'nombre': 'Menú Celíaco Vegetariano',
                'descripcion': 'Menú vegetariano sin TACC',
                'precio': Decimal('1800.00'),
                'activo': True
            }
        )

        # Configuración de menú
        ConfiguracionMenu.objects.get_or_create(
            pk=1,
            defaults={
                'menu_comun': menu_comun,
                'menu_vegetariano': menu_vegetariano,
                'menu_celiaco_comun': menu_celiaco_comun,
                'menu_celiaco_vegetariano': menu_celiaco_vegetariano,
                'requiere_formulario_celiaquia': True
            }
        )

        # ==================== BECAS Y BENEFICIOS ====================
        self.stdout.write(self.style.SUCCESS('\nCreando becas y beneficios...'))

        becas_data = [
            {
                'tipo': 'Beca Comedor',
                'activa': True,
                'tiene_monto': False,
                'permite_comedor': True
            },
            {
                'tipo': 'Beca Residencia',
                'activa': True,
                'tiene_monto': False,
                'permite_comedor': True
            },
            {
                'tipo': 'Beca Estímulo',
                'activa': True,
                'tiene_monto': True,
                'monto_sugerido': Decimal('15000.00'),
                'permite_comedor': True
            }
        ]

        for beca_data in becas_data:
            Beca.objects.get_or_create(
                tipo=beca_data['tipo'],
                defaults=beca_data
            )
            self.stdout.write(f'  ✓ Beca: {beca_data["tipo"]}')

        # Beneficios de comedor
        beneficios_data = [
            {
                'tipo': 'Beca Comedor',
                'tipo_beneficio': 'gratuito',
                'porcentaje_descuento': Decimal('100.00')
            },
            {
                'tipo': 'Beca Residencia',
                'tipo_beneficio': 'gratuito',
                'porcentaje_descuento': Decimal('100.00')
            },
            {
                'tipo': 'Beca Estímulo',
                'tipo_beneficio': 'descuento',
                'porcentaje_descuento': Decimal('50.00')
            }
        ]

        for benef_data in beneficios_data:
            beca = Beca.objects.get(tipo=benef_data['tipo'])
            BeneficioComedor.objects.get_or_create(
                tipo_beca=beca,  # CORREGIDO: era 'beca', ahora es 'tipo_beca'
                defaults={
                    'tipo_beneficio': benef_data['tipo_beneficio'],
                    'porcentaje_descuento': benef_data['porcentaje_descuento']
                }
            )
            self.stdout.write(f'  ✓ Beneficio: {benef_data["tipo"]}')

        # ==================== USUARIOS ====================
        self.stdout.write(self.style.SUCCESS('\nCreando usuarios de prueba...'))

        # 1. SUPERUSUARIO
        user_admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@comedor.uncu.edu.ar',
                'first_name': 'Super',
                'last_name': 'Administrador',
                'is_superuser': True,
                'is_staff': True
            }
        )
        if created:
            user_admin.set_password('admin123')
            user_admin.save()

        # CAMBIO IMPORTANTE: Usar update_or_create en lugar de get_or_create para forzar actualización del rol
        persona_admin, _ = Persona.objects.update_or_create(
            usuario=user_admin,
            defaults={
                'documento': '99999999',
                'nombre': 'Super',
                'apellido': 'Administrador',
                'tipo_documento': 'DNI',
                'correo': 'admin@comedor.uncu.edu.ar',
                'telefono': '2612345678',
                'nacionalidad': 'Argentina',
                'genero': 'prefiero_no_decir',
                'rol': 'admin'  # ROL ASIGNADO EXPLÍCITAMENTE
            }
        )

        self.stdout.write('✓ Admin: admin / admin123')

        # 2. ESTUDIANTES
        estudiantes_data = [
            {
                'username': 'estudiante1',
                'password': 'estudiante123',
                'persona': {
                    'nombre': 'Juan',
                    'apellido': 'Pérez',
                    'documento': '12345678',
                    'correo': 'estudiante1@comedor.uncu.edu.ar',
                    'telefono': '2612345679',
                    'nacionalidad': 'Argentina',
                    'genero': 'masculino'
                },
                'estudiante': {
                    'carrera': 'ING001',
                    'legajo': 'EST001',
                    'anio_ingreso': 2022,
                    'estado': 'R',
                    'preferencia_menu': 'comun'
                },
                'beca': 'Beca Comedor'
            },
            {
                'username': 'estudiante2',
                'password': 'estudiante123',
                'persona': {
                    'nombre': 'María',
                    'apellido': 'Fernández',
                    'documento': '23456789',
                    'correo': 'estudiante2@comedor.uncu.edu.ar',
                    'telefono': '2612345680',
                    'nacionalidad': 'Argentina',
                    'genero': 'femenino'
                },
                'estudiante': {
                    'carrera': 'LIC001',
                    'legajo': 'EST002',
                    'anio_ingreso': 2021,
                    'estado': 'R',
                    'preferencia_menu': 'vegetariano'
                },
                'beca': 'Beca Residencia'
            },
            {
                'username': 'estudiante3',
                'password': 'estudiante123',
                'persona': {
                    'nombre': 'Lucas',
                    'apellido': 'Martínez',
                    'documento': '34567890',
                    'correo': 'estudiante3@comedor.uncu.edu.ar',
                    'telefono': '2612345690',
                    'nacionalidad': 'Argentina',
                    'genero': 'masculino'
                },
                'estudiante': {
                    'carrera': 'MED001',
                    'legajo': 'EST003',
                    'anio_ingreso': 2023,
                    'estado': 'R',
                    'preferencia_menu': 'celiaco_comun'
                },
                'beca': 'Beca Estímulo'
            }
        ]

        for est_data in estudiantes_data:
            user, created = User.objects.get_or_create(
                username=est_data['username'],
                defaults={
                    'email': est_data['persona']['correo'],
                    'first_name': est_data['persona']['nombre'],
                    'last_name': est_data['persona']['apellido']
                }
            )
            if created:
                user.set_password(est_data['password'])
                user.save()

            # CAMBIO: update_or_create para forzar actualización del rol
            persona, _ = Persona.objects.update_or_create(
                usuario=user,
                defaults={
                    'documento': est_data['persona']['documento'],
                    'nombre': est_data['persona']['nombre'],
                    'apellido': est_data['persona']['apellido'],
                    'tipo_documento': 'DNI',
                    'correo': est_data['persona']['correo'],
                    'telefono': est_data['persona']['telefono'],
                    'nacionalidad': est_data['persona']['nacionalidad'],
                    'genero': est_data['persona']['genero'],
                    'rol': 'estudiante'  # ROL EXPLÍCITO
                }
            )

            persona_est, _ = PersonaEstudiante.objects.get_or_create(
                persona=persona,
                defaults={
                    'dependencia': carreras[est_data['estudiante']['carrera']].dependencia,
                    'carrera': carreras[est_data['estudiante']['carrera']],
                    'anio_ingreso': est_data['estudiante']['anio_ingreso'],
                    'numero_legajo': est_data['estudiante']['legajo'],
                    'estado_academico': est_data['estudiante']['estado'],
                    'preferencia_menu': est_data['estudiante']['preferencia_menu']
                }
            )

            # Asignar beca si corresponde
            if est_data.get('beca'):
                beca = Beca.objects.get(tipo=est_data['beca'])
                PersonaBeca.objects.get_or_create(
                    persona_estudiante=persona_est,
                    beca=beca,
                    defaults={
                        'fecha_inicio': date.today() - timedelta(days=30),
                        'fecha_fin': date.today() + timedelta(days=335),
                        'estado_beca': 'ACTIVA',
                        'monto_asignado': beca.monto_sugerido if beca.tiene_monto else None,
                    }
                )

            # Crear certificado celíaco si aplica
            if 'celiaco' in est_data['estudiante']['preferencia_menu']:
                if not CertificadoCeliaco.objects.filter(persona=persona).exists():
                    certificado = CertificadoCeliaco(
                        persona=persona,
                        fecha_emision=date.today() - timedelta(days=60),
                        fecha_vencimiento=date.today() + timedelta(days=305),
                        activo=True,
                        cargado_por=user
                    )
                    # Archivo PDF ficticio para cumplir el campo obligatorio
                    pdf_ficticio = ContentFile(b'%PDF-1.0 CERTIFICADO CELIACO FICTICIO - SOLO PARA PRUEBAS')
                    certificado.archivo_certificado.save(
                        f'certificado_celiaco_{persona.documento}.pdf',
                        pdf_ficticio,
                        save=False
                    )
                    certificado.save()

            self.stdout.write(
                f'✓ Estudiante: {est_data["username"]} / {est_data["password"]} ({est_data.get("beca", "Sin beca")})')

        # 3. INGRESANTE
        user_ing, created = User.objects.get_or_create(
            username='ingresante1',
            defaults={
                'email': 'ingresante1@comedor.uncu.edu.ar',
                'first_name': 'Ana',
                'last_name': 'Torres'
            }
        )
        if created:
            user_ing.set_password('ingresante123')
            user_ing.save()

        # CAMBIO: update_or_create para forzar actualización del rol
        persona_ing, _ = Persona.objects.update_or_create(
            usuario=user_ing,
            defaults={
                'documento': '45678901',
                'nombre': 'Ana',
                'apellido': 'Torres',
                'tipo_documento': 'DNI',
                'correo': 'ingresante1@comedor.uncu.edu.ar',
                'telefono': '2612345681',
                'nacionalidad': 'Argentina',
                'genero': 'femenino',
                'rol': 'ingresante'  # ROL EXPLÍCITO
            }
        )

        PersonaIngresante.objects.get_or_create(
            persona=persona_ing,
            defaults={
                'fecha_vencimiento': date.today() + timedelta(days=180)
            }
        )
        self.stdout.write('✓ Ingresante: ingresante1 / ingresante123')

        # 4. EGRESADO
        user_egr, created = User.objects.get_or_create(
            username='egresado1',
            defaults={
                'email': 'egresado1@comedor.uncu.edu.ar',
                'first_name': 'Roberto',
                'last_name': 'Silva'
            }
        )
        if created:
            user_egr.set_password('egresado123')
            user_egr.save()

        # CAMBIO: update_or_create para forzar actualización del rol
        persona_egr, _ = Persona.objects.update_or_create(
            usuario=user_egr,
            defaults={
                'documento': '56789012',
                'nombre': 'Roberto',
                'apellido': 'Silva',
                'tipo_documento': 'DNI',
                'correo': 'egresado1@comedor.uncu.edu.ar',
                'telefono': '2612345682',
                'nacionalidad': 'Argentina',
                'genero': 'masculino',
                'rol': 'egresado'  # ROL EXPLÍCITO
            }
        )

        PersonaEgresado.objects.get_or_create(persona=persona_egr)
        self.stdout.write('✓ Egresado: egresado1 / egresado123')

        # 5. DOCENTES
        docentes_data = [
            {
                'username': 'docente1',
                'password': 'docente123',
                'persona': {
                    'nombre': 'María',
                    'apellido': 'González',
                    'documento': '67890123',
                    'correo': 'docente1@comedor.uncu.edu.ar',
                    'telefono': '2612345683',
                    'nacionalidad': 'Argentina',
                    'genero': 'femenino'
                },
                'docente': {
                    'legajo': 'DOC001',
                    'categoria': 'ADJUNTO',
                    'dependencia': 'FI',
                    'fecha_ingreso': date(2020, 3, 1)
                }
            },
            {
                'username': 'docente2',
                'password': 'docente123',
                'persona': {
                    'nombre': 'Pedro',
                    'apellido': 'Ramírez',
                    'documento': '78901234',
                    'correo': 'docente2@comedor.uncu.edu.ar',
                    'telefono': '2612345684',
                    'nacionalidad': 'Argentina',
                    'genero': 'masculino'
                },
                'docente': {
                    'legajo': 'DOC002',
                    'categoria': 'TITULAR',
                    'dependencia': 'FCEN',
                    'fecha_ingreso': date(2015, 8, 15)
                }
            }
        ]

        for doc_data in docentes_data:
            user, created = User.objects.get_or_create(
                username=doc_data['username'],
                defaults={
                    'email': doc_data['persona']['correo'],
                    'first_name': doc_data['persona']['nombre'],
                    'last_name': doc_data['persona']['apellido']
                }
            )
            if created:
                user.set_password(doc_data['password'])
                user.save()

            # CAMBIO: update_or_create para forzar actualización del rol
            persona, _ = Persona.objects.update_or_create(
                usuario=user,
                defaults={
                    'documento': doc_data['persona']['documento'],
                    'nombre': doc_data['persona']['nombre'],
                    'apellido': doc_data['persona']['apellido'],
                    'tipo_documento': 'DNI',
                    'correo': doc_data['persona']['correo'],
                    'telefono': doc_data['persona']['telefono'],
                    'nacionalidad': doc_data['persona']['nacionalidad'],
                    'genero': doc_data['persona']['genero'],
                    'rol': 'docente'  # ROL EXPLÍCITO
                }
            )

            PersonaDocente.objects.get_or_create(
                persona=persona,
                defaults={
                    'numero_legajo': doc_data['docente']['legajo'],
                    'categoria_docente': doc_data['docente']['categoria'],
                    'fecha_ingreso_docencia': doc_data['docente']['fecha_ingreso'],
                    'dependencia': dependencias[doc_data['docente']['dependencia']]
                }
            )

            self.stdout.write(f'✓ Docente: {doc_data["username"]} / {doc_data["password"]}')

        # 6. NO DOCENTES
        nodocentes_data = [
            {
                'username': 'nodocente1',
                'password': 'nodocente123',
                'persona': {
                    'nombre': 'Carlos',
                    'apellido': 'Rodríguez',
                    'documento': '89012345',
                    'correo': 'nodocente1@comedor.uncu.edu.ar',
                    'telefono': '2612345685',
                    'nacionalidad': 'Argentina',
                    'genero': 'masculino'
                },
                'nodocente': {
                    'legajo': 'NOD001',
                    'cargo': 'Administrativo',
                    'area': 'Administración',
                    'tipo_contrato': 'PLANTA_PERMANENTE',
                    'fecha_ingreso': date(2019, 6, 15),
                    'fecha_fin': date(2029, 6, 15)
                }
            },
            {
                'username': 'nodocente2',
                'password': 'nodocente123',
                'persona': {
                    'nombre': 'Silvia',
                    'apellido': 'López',
                    'documento': '90123456',
                    'correo': 'nodocente2@comedor.uncu.edu.ar',
                    'telefono': '2612345686',
                    'nacionalidad': 'Argentina',
                    'genero': 'femenino'
                },
                'nodocente': {
                    'legajo': 'NOD002',
                    'cargo': 'Bibliotecaria',
                    'area': 'Biblioteca',
                    'tipo_contrato': 'CONTRATADO',
                    'fecha_ingreso': date(2021, 3, 1),
                    'fecha_fin': date(2028, 3, 1)
                }
            }
        ]

        for nod_data in nodocentes_data:
            user, created = User.objects.get_or_create(
                username=nod_data['username'],
                defaults={
                    'email': nod_data['persona']['correo'],
                    'first_name': nod_data['persona']['nombre'],
                    'last_name': nod_data['persona']['apellido']
                }
            )
            if created:
                user.set_password(nod_data['password'])
                user.save()

            # CAMBIO: update_or_create para forzar actualización del rol
            persona, _ = Persona.objects.update_or_create(
                usuario=user,
                defaults={
                    'documento': nod_data['persona']['documento'],
                    'nombre': nod_data['persona']['nombre'],
                    'apellido': nod_data['persona']['apellido'],
                    'tipo_documento': 'DNI',
                    'correo': nod_data['persona']['correo'],
                    'telefono': nod_data['persona']['telefono'],
                    'nacionalidad': nod_data['persona']['nacionalidad'],
                    'genero': nod_data['persona']['genero'],
                    'rol': 'no_docente'  # ROL EXPLÍCITO
                }
            )

            PersonaNoDocente.objects.get_or_create(
                persona=persona,
                defaults={
                    'numero_legajo': nod_data['nodocente']['legajo'],
                    'cargo': nod_data['nodocente']['cargo'],
                    'fecha_ingreso_laboral': nod_data['nodocente']['fecha_ingreso'],
                    'fecha_finalizacion_laboral': nod_data['nodocente']['fecha_fin'],
                    'tipo_contrato': nod_data['nodocente']['tipo_contrato'],
                    'area_principal': areas[nod_data['nodocente']['area']]
                }
            )

            self.stdout.write(f'✓ No Docente: {nod_data["username"]} / {nod_data["password"]}')

        # 7. ADMINISTRADOR DE COMEDOR
        user_admin, created = User.objects.get_or_create(
            username='admin_comedor',
            defaults={
                'email': 'admin.comedor@comedor.uncu.edu.ar',
                'first_name': 'Administrador',
                'last_name': 'Comedor',
                'is_staff': True
            }
        )
        if created:
            user_admin.set_password('admincomedor123')
            user_admin.save()

        # CAMBIO: update_or_create para forzar actualización del rol
        persona_admin, _ = Persona.objects.update_or_create(
            usuario=user_admin,
            defaults={
                'documento': '01234567',
                'nombre': 'Administrador',
                'apellido': 'Comedor',
                'tipo_documento': 'DNI',
                'correo': 'admin.comedor@comedor.uncu.edu.ar',
                'telefono': '2612345687',
                'nacionalidad': 'Argentina',
                'genero': 'prefiero_no_decir',
                'rol': 'admin_comedor'  # ROL EXPLÍCITO
            }
        )

        self.stdout.write('✓ Admin Comedor: admin_comedor / admincomedor123')

        # RESUMEN FINAL
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE USUARIOS CREADOS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('\n📋 ADMINISTRATIVOS:')
        self.stdout.write('  • admin / admin123 (Superusuario)')
        self.stdout.write('  • admin_comedor / admincomedor123 (Administrador de Comedor)')

        self.stdout.write('\n🎓 ESTUDIANTES:')
        self.stdout.write('  • estudiante1 / estudiante123 (Con Beca Comedor - Gratuito)')
        self.stdout.write('  • estudiante2 / estudiante123 (Con Beca Residencia - Gratuito)')
        self.stdout.write('  • estudiante3 / estudiante123 (Con Beca Estímulo - 50% descuento, Celíaco)')
        self.stdout.write('  • ingresante1 / ingresante123 (Ingresante sin beca)')
        self.stdout.write('  • egresado1 / egresado123 (Egresado - Invitado)')

        self.stdout.write('\n👨‍🏫 DOCENTES:')
        self.stdout.write('  • docente1 / docente123 (Profesor Adjunto - Ingeniería)')
        self.stdout.write('  • docente2 / docente123 (Profesor Titular - Cs. Exactas)')

        self.stdout.write('\n👷 NO DOCENTES:')
        self.stdout.write('  • nodocente1 / nodocente123 (Administrativo)')
        self.stdout.write('  • nodocente2 / nodocente123 (Bibliotecaria)')

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ Proceso completado exitosamente'))
        self.stdout.write(self.style.SUCCESS('=' * 70))