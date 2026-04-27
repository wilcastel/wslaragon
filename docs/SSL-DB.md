# 🔒 SSL y Base de Datos

Esta sección detalla los aspectos más importantes para que tus sitios funcionen con el candado verde y cómo se gestionan las bases de datos.

## 1. Confianza SSL en Windows (Candado Verde)

### Cómo funciona el SSL en WSLaragon

WSLaragon genera certificados SSL para cada sitio usando **openssl**, firmados por una **Autoridad Certificante (CA) root local** creada por `mkcert`. Esto tiene ventajas sobre usar solo `mkcert`:

- **CN correcto**: El certificado incluye el Nombre Común (CN) con el dominio real (ej: `CN=misitio.test`)
- **SANs completos**: Incluye `DNS:misitio.test` e `IP:127.0.0.1` como Subject Alternative Names
- **Firma consistente**: Todos los certificados están firmados por la misma CA root local

### Paso A: Instalar la CA Root en Windows (⚠️ REQUERIDO)

**Sin este paso, los navegadores mostrarán "Conexión no segura".**

1. Copiá la CA root a Windows:
   ```bash
   cp $(mkcert -CAROOT)/rootCA.pem /mnt/c/Users/TuUsuario/Desktop/rootCA.crt
   ```

2. En Windows, hacé doble clic en `rootCA.crt` en el escritorio

3. Seleccioná **"Instalar certificado..."** → **"Equipo local"** → **"Colocar todos los certificados en el siguiente almacén"** → **"Entidades de certificación raíz de confianza"**

4. **Reiniciá el navegador completamente** (cerrá todas las ventanas)

### Paso B: Verificación

Después de instalar la CA, verificá que el certificado funciona:

```bash
# Crear un sitio de prueba
wslaragon site create prueba --php --ssl

# Verificar que el CN del certificado es correcto
openssl x509 -in ~/.wslaragon/ssl/prueba.test.pem -text -noout | grep Subject:
# Resultado esperado: Subject: CN = prueba.test, O = WSLaragon Development, C = US

# Verificar la cadena de confianza
openssl verify -CAfile ~/.wslaragon/ssl/rootCA.pem ~/.wslaragon/ssl/prueba.test.pem
# Resultado esperado: OK
```

### Verificar desde Windows

Abrí `https://prueba.test` en tu navegador. Deberías ver el 🔒 candado verde sin advertencias de seguridad.

> **Nota**: Si acabás de instalar la CA y sigue sin funcionar, limpiá el caché SSL del navegador:
> - **Chrome/Edge**: `chrome://net-internals/#hsts` → eliminá la entrada del dominio
> - O usá `Ctrl+Shift+Delete` → limpiar caché

### Solución de problemas SSL

| Problema | Causa | Solución |
|----------|-------|----------|
| "Conexión no segura" en navegador | CA root no instalada en Windows | Seguí el Paso A arriba |
| `CN = mkcert development certificate` | Certificado viejo generado con mkcert puro | Regenerá el certificado: `wslaragon ssl generate dominio.test` |
| `ERR_CERT_AUTHORITY_INVALID` | CA root no está en el almacén de Windows | Verificá en `certlm.msc` que esté en "Entidades de certificación raíz de confianza" |
| `ERR_SSL_PROTOCOL_ERROR` | Nginx no tiene configuración SSL | Verificá con `wslaragon doctor` |

## 2. Generación de Certificados

### Crear certificado durante la creación del sitio

Los certificados SSL se generan automáticamente al crear un sitio (a menos que uses `--no-ssl`):

```bash
# SSL habilitado por defecto
wslaragon site create mi-proyecto --php --mysql

# Sin SSL
wslaragon site create mi-proyecto --php --no-ssl
```

### Crear certificado manualmente

```bash
wslaragon ssl generate midominio.test
```

Esto genera:
- `~/.wslaragon/ssl/midominio.test.pem` — Certificado
- `~/.wslaragon/ssl/midominio.test-key.pem` — Clave privada

### ¿Cómo se generan los certificados?

WSLaragon NO usa `mkcert` directamente para generar los certificados de los sitios. En su lugar:

1. **CA Root**: Se crea con `mkcert -install`, que genera y confía la CA local
2. **Certificados de sitio**: Se generan con `openssl`, creando una clave privada RSA 2048, un CSR con el CN del dominio, y firmando con la CA root

Esto garantiza que el campo **Subject** del certificado contenga `CN=misitio.test` en vez del CN genérico que genera `mkcert` por defecto.

## 3. MariaDB (MySQL)

### Configuración del Usuario Root

WSLaragon usa el usuario `root` para crear bases de datos. Asegurate de que el método de autenticación sea mediante contraseña y no `unix_socket`.

Para sincronizar la contraseña con tu `.env`:
```bash
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'tu_contraseña_del_env'; FLUSH PRIVILEGES;"
```

### Bases de Datos de Sitios

Cuando creas un sitio con `--mysql`, WSLaragon:
1. Crea una base de datos con el nombre `{site_name}_db`.
2. Configura el juego de caracteres como `utf8mb4_unicode_ci`.

**WordPress crea la base de datos automáticamente** — no necesitás especificar `--mysql`:

```bash
# ✅ Correcto — WordPress crea la DB automáticamente
wslaragon site create mi-blog --wordpress

# ❌ Innecesario — --mysql ya está implícito en WordPress
wslaragon site create mi-blog --wordpress --mysql
```

### phpMyAdmin — Gestión Visual de Bases de Datos

Para administrar tus bases de datos desde una interfaz web:

```bash
# Crear sitio phpMyAdmin (no necesita base de datos propia)
wslaragon site create pma --phpmyadmin --ssl
```

Accedé a `https://pma.test` para gestionar todas tus bases de datos MySQL visualmente.

> **Nota**: phpMyAdmin no crea su propia base de datos — se conecta a MySQL usando las credenciales configuradas en tu `.env`.

---

> [!TIP]
> Si tenés problemas de conexión, verificá que el servicio esté corriendo con `wslaragon service status`.