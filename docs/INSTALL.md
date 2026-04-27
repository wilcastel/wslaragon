# 🛠️ Guía de Instalación

Esta guía asume que ya tienes instalado WSL2 con Ubuntu 22.04 o superior.

## 1. Requisitos del Sistema

WSLaragon requiere los siguientes servicios instalados en tu Ubuntu:

- **Servidor Web**: Nginx
- **Base de Datos**: MariaDB / MySQL
- **PHP**: PHP 8.1+ (recomendado 8.3) con FPM
- **Otras**: `mkcert` (para SSL local) y `openssl` (incluido en Ubuntu)

## 2. Instalación de WSLaragon

Sigue estos pasos para instalar el CLI de forma global:

```bash
# Clona el repositorio
git clone https://github.com/tu-usuario/wslaragon.git
cd wslaragon

# Crea y activa el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instala las dependencias
pip install -e .

# Crea el enlace global
sudo ln -sf $(pwd)/venv/bin/wslaragon /usr/local/bin/wslaragon
```

## 3. Configuración Inicial

WSLaragon utiliza un archivo `.env` para gestionar las credenciales de forma segura.

1.  Copia la plantilla de ejemplo:
    ```bash
    cp .env.example .env
    ```
2.  Edita el archivo `.env` y configura tu contraseña de base de datos:
    ```text
    DB_USER=root
    DB_PASSWORD=tu_contraseña_segura
    ```

## 4. Instalar la CA Root para SSL (⚠️ IMPORTANTE)

Para que los navegadores en Windows confíen en los certificados SSL de tus sitios `.test`, **debés instalar la Autoridad Certificante (CA) root en el almacén de certificados de Windows**. Sin este paso, los sitios mostrarán "Conexión no segura" en el navegador.

### ¿Por qué es necesario?

WSLaragon genera certificados SSL firmados por una CA local propia. El navegador en Windows no confía en esta CA por defecto — necesitás instalarla manualmente como una "Entidad de certificación raíz de confianza".

WSLaragon genera los certificados usando `openssl`, firmando con la CA local que crea `mkcert`. Esto garantiza que el **Nombre Común (CN)** del certificado contenga el dominio correcto (ej: `CN=misitio.test`), a diferencia de `mkcert` que usa un CN genérico.

### Paso A: Generar la CA local

```bash
# Instalar mkcert (si no lo tenés)
curl -L https://dl.filippo.io/mkcert/latest?for=linux/amd64 -o mkcert
chmod +x mkcert && sudo mv mkcert /usr/local/bin/

# Crear e instalar la CA local en WSL
mkcert -install
```

### Paso B: Copiar la CA al escritorio de Windows

```bash
# Reemplazá "TuUsuario" por tu carpeta de usuario en Windows
cp $(mkcert -CAROOT)/rootCA.pem /mnt/c/Users/TuUsuario/Desktop/rootCA.crt
```

> **Tip**: Si no sabés tu nombre de usuario en Windows, ejecutá `ls /mnt/c/Users/` para ver las carpetas disponibles.

### Paso C: Importar la CA en Windows

1. En Windows, abrí el archivo `rootCA.crt` que está en el escritorio
2. Hacé clic en **"Instalar certificado..."**
3. Seleccioná **"Equipo local"** (requiere permisos de administrador)
4. Seleccioná **"Colocar todos los certificados en el siguiente almacén"**
5. Navegá hasta **"Entidades de certificación raíz de confianza"**
6. Confirmá la instalación

> **Alternativa automática**: WSLaragon intenta instalar la CA automáticamente al generar certificados, pero requiere permisos de administrador en Windows. Si funciona, verás una ventana de UAC pidiendo confirmación.

### Paso D: Reiniciar el navegador

**Cerrá completamente** el navegador (Chrome, Edge, Firefox) y volvelo a abrir. Los navegadores cachean los certificados y no actualizan el almacén hasta reiniciar.

> Si después de reiniciar sigue sin el candado verde, limpiá el caché del navegador con `Ctrl+Shift+Delete`.

### Verificar que funciona

```bash
# Crear un sitio de prueba
wslaragon site create prueba --php --ssl

# Verificar el certificado tiene el CN correcto
openssl x509 -in ~/.wslaragon/ssl/prueba.test.pem -text -noout | grep Subject:
# Debería mostrar: Subject: CN = prueba.test, O = WSLaragon Development, C = US
```

Si ves `CN = prueba.test` en el Subject, el certificado está bien generado. Abrí `https://prueba.test` en tu navegador y deberías ver el 🔒 candado verde.

## 5. Permisos de Administrador (SUDO)

Para que WSLaragon pueda crear sitios sin pedirte contraseña cada vez, ejecuta:

```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /usr/sbin/service, /bin/systemctl, /usr/bin/phpenmod, /usr/bin/phpdismod, /bin/cp, /bin/ln, /bin/rm, /usr/bin/tee" | sudo tee /etc/sudoers.d/wslaragon
```

> **Nota sobre `sudo`**: WSLaragon detecta automáticamente el usuario real incluso cuando se ejecuta con `sudo`, usando la variable `SUDO_USER`. Esto significa que los archivos del sitio siempre se crearán en tu carpeta `/home/tu-usuario/web/`, no en `/root/web/`.

---

## 6. Verificar la Instalación

```bash
# Verificar que todo está en orden
wslaragon doctor

# Verificar los servicios
wslaragon service status

# Verificar la CA root de SSL
wslaragon ssl list
```

---

¡Listo! Ahora puedes empezar a usar el comando `wslaragon` desde cualquier lugar.

## Solución de Problemas de Instalación

### El certificado SSL no aparece como válido en Windows

1. Verificá que la CA root esté instalada: abrí `certlm.msc` en Windows y buscá "mkcert" o "WSLaragon" en **Entidades de certificación raíz de confianza**
2. Si no está, repetí el **Paso C** de la sección 4
3. Reiniciá el navegador completamente

### Los sitios muestran 403 Permission Denied

```bash
# Arreglar permisos del directorio home
chmod 755 $HOME

# O usar el comando de wslaragon
wslaragon site fix-permissions misitio
```

### `sudo wslaragon` crea archivos en `/root/` en vez de `/home/`

No pasa más — WSLaragon ahora detecta `SUDO_USER` para resolver el directorio home correcto. Si tenés una versión anterior, actualizá con `pip install -e .`.