from django.db import models
from decimal import Decimal


# ─────────────────────────────────────────────────────────
# Constantes compartidas
# ─────────────────────────────────────────────────────────

MODALIDADES = [
    ('presencial', 'Presencial'),
    ('online', 'Online'),
]


class Categoria(models.Model):
    """
    Categoría de cursos. Por defecto: Empresariales, Técnico, Vacacionales.
    Pero el usuario puede agregar las que quiera.
    """
    COLORES = [
        ('#1a237e', 'Azul'),
        ('#2e7d32', 'Verde'),
        ('#c62828', 'Rojo'),
        ('#f0ad4e', 'Naranja'),
        ('#6a1b9a', 'Morado'),
        ('#00838f', 'Cian'),
        ('#5d4037', 'Marrón'),
        ('#455a64', 'Gris'),
    ]

    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(
        max_length=7, choices=COLORES, default='#1a237e',
        help_text='Color con el que se identifica la categoría.'
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text='Orden de aparición (menor = primero).'
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """
    Cursos que se ofertan. Cada uno puede ofrecerse en modalidad presencial,
    online, o en ambas. Cada modalidad tiene su propio valor.
    """

    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT,
        related_name='cursos', null=True, blank=True,
    )
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)

    # Modalidades que ofrece el curso
    ofrece_presencial = models.BooleanField(
        default=True,
        help_text='Marcar si el curso se ofrece en modalidad presencial.'
    )
    ofrece_online = models.BooleanField(
        default=False,
        help_text='Marcar si el curso se ofrece en modalidad online.'
    )

    # Valores diferenciados por modalidad
    valor_presencial = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Costo del curso presencial (USD).'
    )
    valor_online = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='Costo del curso online (USD).'
    )

    # Campo legado (se conserva para no romper datos antiguos).
    # NO se usa para nuevas matrículas; el código siempre debe leer
    # valor_presencial / valor_online según la modalidad.
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text='[Legado] Valor único anterior. Reemplazado por valor_presencial / valor_online.'
    )

    duracion = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['categoria__orden', 'nombre']

    def valor_para(self, modalidad):
        """Devuelve el valor del curso según la modalidad."""
        if modalidad == 'online':
            return self.valor_online
        return self.valor_presencial

    def ofrece(self, modalidad):
        """¿El curso se ofrece en esa modalidad?"""
        if modalidad == 'online':
            return self.ofrece_online
        return self.ofrece_presencial

    @property
    def modalidades_etiqueta(self):
        """Texto corto que indica las modalidades disponibles."""
        partes = []
        if self.ofrece_presencial:
            partes.append('Presencial')
        if self.ofrece_online:
            partes.append('Online')
        return ' + '.join(partes) if partes else '— Sin modalidad —'

    def __str__(self):
        # Mostrar el valor más relevante (prioriza presencial si lo ofrece)
        v = self.valor_presencial if self.ofrece_presencial else self.valor_online
        return f'{self.nombre} (${v})'


class JornadaCurso(models.Model):
    """
    Cada curso puede tener varias jornadas (fecha + horario + ciudad/zona).
    Estas son las opciones que el estudiante elige al matricularse.
    Cada jornada pertenece a una modalidad (presencial u online).
    """
    curso = models.ForeignKey(
        Curso, on_delete=models.CASCADE, related_name='jornadas'
    )
    modalidad = models.CharField(
        max_length=20, choices=MODALIDADES, default='presencial',
        help_text='Modalidad de esta jornada.'
    )
    descripcion = models.CharField(
        max_length=200,
        help_text='Ej.: Sábados intensivos, Domingos intensivos…'
    )
    fecha_inicio = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    ciudad = models.CharField(
        max_length=100,
        help_text='Ciudad (presencial) o zona horaria/plataforma (online).'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Jornada'
        verbose_name_plural = 'Jornadas'
        ordering = ['curso', 'modalidad', 'fecha_inicio']

    @property
    def etiqueta(self):
        prefijo = '🟢 Online' if self.modalidad == 'online' else '🏫 Presencial'
        return (
            f'{prefijo} – {self.descripcion.upper()} – '
            f'{self.fecha_inicio.strftime("%d/%m/%Y")} – '
            f'{self.hora_inicio.strftime("%H:%M")} a {self.hora_fin.strftime("%H:%M")} '
            f'({self.ciudad})'
        )

    def __str__(self):
        return self.etiqueta


class Estudiante(models.Model):
    """Datos personales del estudiante."""

    NIVELES_FORMACION = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Bachillerato / Secundaria'),
        ('tecnico', 'Técnico'),
        ('tecnologo', 'Tecnólogo'),
        ('tercer_nivel', 'Tercer Nivel (Pregrado)'),
        ('cuarto_nivel', 'Cuarto Nivel (Posgrado)'),
        ('otro', 'Otro'),
    ]

    cedula = models.CharField(max_length=20, unique=True)
    apellidos = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    edad = models.PositiveIntegerField(null=True, blank=True)
    correo = models.EmailField(blank=True)
    celular = models.CharField(max_length=20, blank=True)
    nivel_formacion = models.CharField(
        max_length=20, choices=NIVELES_FORMACION, blank=True
    )
    titulo_profesional = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['apellidos', 'nombres']

    @property
    def nombre_completo(self):
        return f'{self.apellidos} {self.nombres}'.strip()

    def __str__(self):
        return f'{self.cedula} – {self.nombre_completo}'


class Matricula(models.Model):
    """Matrícula que une estudiante + curso + jornada + pago."""

    TALLAS_CAMISETA = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('NA', 'Ninguna de las anteriores (la academia solo cubre hasta XL)'),
    ]

    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.PROTECT, related_name='matriculas'
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name='matriculas'
    )
    jornada = models.ForeignKey(
        JornadaCurso, on_delete=models.PROTECT,
        related_name='matriculas', null=True, blank=True,
        help_text='Fecha y horario seleccionados (depende del curso y modalidad).'
    )
    modalidad = models.CharField(
        max_length=20, choices=MODALIDADES, default='presencial'
    )
    fecha_matricula = models.DateField()
    talla_camiseta = models.CharField(
        max_length=2, choices=TALLAS_CAMISETA, blank=True
    )
    valor_curso = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Se autocompleta con el valor del curso según modalidad, pero puedes ajustarlo.'
    )
    valor_pagado = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    observaciones = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    # Auditoría: qué usuario registró la matrícula (útil para asesores)
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='matriculas_registradas',
        help_text='Usuario que registró la matrícula (admin o asesor).'
    )

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        ordering = ['-fecha_matricula', '-creado']

    @property
    def saldo(self):
        return (self.valor_curso or Decimal('0.00')) - (self.valor_pagado or Decimal('0.00'))

    @property
    def estado_pago(self):
        if self.saldo <= 0:
            return 'Pagado'
        if self.valor_pagado and self.valor_pagado > 0:
            return 'Parcial'
        return 'Pendiente'

    @property
    def horario(self):
        if self.jornada:
            return f'{self.jornada.hora_inicio.strftime("%H:%M")} – {self.jornada.hora_fin.strftime("%H:%M")}'
        return '—'

    @property
    def sede(self):
        return self.jornada.ciudad if self.jornada else '—'

    def recalcular_valor_pagado(self, save=True):
        """
        Recalcula valor_pagado como la suma de todos los abonos.
        Se llama automáticamente al guardar/eliminar un Abono.
        """
        total = self.abonos.aggregate(s=models.Sum('monto'))['s'] or Decimal('0.00')
        self.valor_pagado = total
        if save:
            super().save(update_fields=['valor_pagado', 'actualizado'])
        return total

    def save(self, *args, **kwargs):
        # Si no se asignó valor_curso, tomar el valor de la modalidad
        if not self.valor_curso and self.curso_id:
            self.valor_curso = self.curso.valor_para(self.modalidad)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.estudiante} – {self.curso} ({self.get_modalidad_display()})'


class Abono(models.Model):
    """
    Cada pago parcial o completo que hace un estudiante para una matrícula.
    La suma de todos los abonos = valor_pagado de la matrícula.
    """

    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
    ]

    matricula = models.ForeignKey(
        Matricula, on_delete=models.CASCADE, related_name='abonos'
    )
    fecha = models.DateField(
        help_text='Fecha en que se recibió el abono.'
    )
    monto = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Cantidad recibida en este abono (USD).'
    )
    metodo = models.CharField(
        max_length=20, choices=METODOS_PAGO, default='efectivo',
        help_text='Forma en que se realizó el pago.'
    )
    numero_recibo = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text='Número de comprobante. Si se deja vacío, se genera automáticamente.'
    )
    observaciones = models.TextField(blank=True)

    # Auditoría
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='abonos_registrados',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Abono'
        verbose_name_plural = 'Abonos'
        ordering = ['-fecha', '-creado']

    @staticmethod
    def generar_numero_recibo():
        """Genera el siguiente número de recibo correlativo: REC-0001, REC-0002…"""
        ultimo = Abono.objects.filter(
            numero_recibo__startswith='REC-'
        ).order_by('-numero_recibo').first()

        if ultimo and ultimo.numero_recibo[4:].isdigit():
            siguiente = int(ultimo.numero_recibo[4:]) + 1
        else:
            siguiente = 1
        return f'REC-{siguiente:04d}'

    def save(self, *args, **kwargs):
        # Auto-generar número de recibo si está vacío
        if not self.numero_recibo:
            self.numero_recibo = Abono.generar_numero_recibo()
        super().save(*args, **kwargs)
        # Recalcular el total pagado de la matrícula
        if self.matricula_id:
            self.matricula.recalcular_valor_pagado()

    def delete(self, *args, **kwargs):
        matricula = self.matricula
        super().delete(*args, **kwargs)
        # Recalcular después de eliminar
        matricula.recalcular_valor_pagado()

    def __str__(self):
        return f'{self.numero_recibo} — ${self.monto} ({self.fecha})'
